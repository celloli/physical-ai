"""起動: python -m streamlit run app.py"""

import json
import sqlite3
from datetime import date
from urllib.parse import urlparse

import streamlit as st

import database as db
from learning import FIELDS, STATUS_PROGRESS, progress, today_tasks

st.set_page_config(page_title="Physical AI Learning", page_icon="📘", layout="wide")
db.initialize()


def save(action):
    """入力エラーを画面に表示し、成功時は再読み込みして一覧も更新する。"""
    try:
        action()
    except sqlite3.IntegrityError:
        st.error("同じ分野・名前のトピック、または同じ成果物が登録済みです。入力内容を確認してください。")
    except ValueError as error:
        st.error(str(error))
    else:
        st.session_state["notice"] = "保存しました。"
        st.rerun()


def topic_label(topic):
    return f"{topic['field']} / {topic['name']}"


def dashboard(topics):
    st.title("学びを、次の一歩へ。")
    st.caption("Physical AI Learning · 学習の現在地と、今日取り組むこと")
    cols = st.columns(3)
    cols[0].metric("全体の進捗", f"{progress(topics)}%")
    cols[1].metric("完了したトピック", f"{sum(t['status'] == '完了' for t in topics)} / {len(topics)}")
    cols[2].metric("現在学習中", sum(t["status"] == "学習中" for t in topics))
    st.subheader("今日やること")
    st.caption("学習中を優先したおすすめです。「次にやること」を入力すると、ここに反映されます。")
    tasks = today_tasks(topics)
    if not tasks:
        st.success("登録済みのトピックはすべて完了です。次に学ぶトピックを追加しましょう。")
    for index, (topic, action) in enumerate(tasks, 1):
        with st.container(border=True):
            st.write(f"**{index}. {topic_label(topic)}**")
            st.write(action)

    left, right = st.columns([3, 2])
    with left:
        st.subheader("分野ごとの進捗")
        st.caption("状態の到達度を平均：未学習0 / 学習中25 / 概念理解50 / 実装済み75 / 完了100%")
        fields = list(dict.fromkeys(FIELDS + [t["field"] for t in topics]))
        for field in fields:
            group = [t for t in topics if t["field"] == field]
            with st.container(border=True):
                st.write(f"**{field}**")
                if group:
                    value = progress(group)
                    st.progress(value, text=f"{value}% · 完了 {sum(t['status'] == '完了' for t in group)}/{len(group)}")
                else:
                    st.caption("トピック未登録 · トピック画面から追加できます")
    with right:
        st.subheader("現在学習中")
        active = [t for t in topics if t["status"] == "学習中"]
        if not active:
            st.info("トピックの状態を「学習中」にすると表示されます。")
        for topic in active:
            with st.container(border=True):
                st.markdown(":green[● 学習中]")
                st.write(f"**{topic['name']}**")
                st.caption(topic["field"])
                rating = topic["understanding"]
                st.write(f"理解度：{rating}/5" if rating else "理解度：未評価")
                if topic["next_action"]:
                    st.write(topic["next_action"])


def topics_page(topics):
    st.title("学習トピック")
    fields = list(dict.fromkeys(FIELDS + [t["field"] for t in topics]))
    a, b = st.columns(2)
    field_filter = a.selectbox("分野で絞り込む", ["すべて"] + fields)
    status_filter = b.selectbox("状態で絞り込む", ["すべて"] + list(STATUS_PROGRESS))
    filtered = [t for t in topics if (field_filter == "すべて" or t["field"] == field_filter)
                and (status_filter == "すべて" or t["status"] == status_filter)]
    if filtered:
        st.dataframe([{
            "分野": t["field"], "トピック": t["name"], "状態": t["status"],
            "理解度": str(t["understanding"]) if t["understanding"] else "未評価",
            "次にやること": t["next_action"],
        } for t in filtered], hide_index=True, use_container_width=True)
    else:
        st.info("条件に合うトピックがありません。新しいトピックも追加できます。")
    selected = st.selectbox("追加・編集するトピック", [None] + filtered,
                            format_func=lambda t: "＋ 新規トピック" if t is None else topic_label(t))
    topic = selected or {"field": fields[0], "name": "", "status": "未学習",
                         "understanding": None, "notes": "", "next_action": ""}
    # トピックごとにフォームのキーを変えて、前の入力が残るのを防ぐ。
    with st.form(f"topic_{topic.get('id', 'new')}"):
        field = st.selectbox("分野", fields, index=fields.index(topic["field"]))
        custom = st.text_input("分野を新しく作る場合は入力（こちらを優先）")
        name = st.text_input("トピック名", topic["name"])
        status = st.selectbox("状態", list(STATUS_PROGRESS), index=list(STATUS_PROGRESS).index(topic["status"]))
        understanding = st.selectbox("理解度", [None, 1, 2, 3, 4, 5],
                                      index=[None, 1, 2, 3, 4, 5].index(topic["understanding"]),
                                      format_func=lambda x: "未評価" if x is None else str(x))
        st.caption("1：説明できない / 2：見覚えがある / 3：要点を説明できる / 4：応用できる / 5：人に教えられる")
        notes = st.text_area("メモ", topic["notes"])
        next_action = st.text_area("次にやること", topic["next_action"])
        if st.form_submit_button("トピックを保存", type="primary"):
            save(lambda: db.save_topic(custom.strip() or field, name, status, understanding, notes, next_action, topic.get("id")))

    if selected:
        st.subheader("関連する成果物")
        st.caption("ROS 2コード・VLA実験・自主プロジェクトなど。URLやパスの存在確認・自動同期は行いません。")
        for artifact in db.list_artifacts(selected["id"]):
            with st.container(border=True):
                st.write(artifact["label"])
                location = artifact["location"]
                if urlparse(location).scheme in ("https", "http") and urlparse(location).netloc:
                    st.link_button("成果物を開く", location)
                else:
                    st.code(location, language=None)
        with st.form(f"artifact_{selected['id']}", clear_on_submit=True):
            label = st.text_input("成果物の名前")
            location = st.text_input("URL または ローカルパス")
            if st.form_submit_button("成果物を追加"):
                save(lambda: db.save_artifact(selected["id"], label, location))


def logs_page():
    st.title("学習ログ")
    st.caption("1日1件。過去の日付を選ぶと、その日の内容を読み込んで編集できます。")
    day = st.date_input("記録する日付", value=date.today())
    logs = db.list_logs()
    entry = next((row for row in logs if row["day"] == day.isoformat()), {})
    with st.form(f"log_{day}"):
        learned = st.text_area("今日学んだこと", entry.get("learned", ""))
        practiced = st.text_area("実際に手を動かしたこと", entry.get("practiced", ""))
        unclear = st.text_area("分からなかったこと", entry.get("unclear", ""))
        next_action = st.text_area("次回やること", entry.get("next_action", ""))
        if st.form_submit_button("学習ログを保存", type="primary"):
            save(lambda: db.save_log(day, learned, practiced, unclear, next_action))
    st.subheader("これまでの記録")
    if not logs:
        st.info("最初の学習ログを残してみましょう。1項目だけでも保存できます。")
    for row in logs:
        with st.expander(row["day"]):
            for label, key in [("今日学んだこと", "learned"), ("実際に手を動かしたこと", "practiced"),
                               ("分からなかったこと", "unclear"), ("次回やること", "next_action")]:
                st.write(f"**{label}**")
                st.write(row[key] or "—")


def questions_page(topics):
    st.title("理解度チェック")
    st.caption("自分で問題と回答を登録して振り返ります。自動採点はありません。問題の理解度はトピックの理解度と別に保存します。")
    if not topics:
        st.info("先にトピックを登録してください。")
        return
    topic = st.selectbox("確認するトピック", topics, format_func=topic_label)
    questions = db.list_questions(topic["id"])
    for question in questions:
        with st.container(border=True):
            st.write(f"**{question['question']}**")
            st.caption(f"自己評価：{question['understanding']}/5")
            with st.expander("回答を表示"):
                st.write(question["answer"] or "まだ回答していません。")
    selected = st.selectbox("追加・編集する問題", [None] + questions,
                            format_func=lambda q: "＋ 新規問題" if q is None else q["question"],
                            key=f"question_choice_{topic['id']}")
    current = selected or {"question": "", "answer": "", "understanding": 1}
    with st.form(f"question_{topic['id']}_{current.get('id', 'new')}"):
        question = st.text_area("問題", current["question"])
        answer = st.text_area("自分の回答", current["answer"])
        understanding = st.slider("この問題の理解度", 1, 5, current["understanding"])
        if st.form_submit_button("確認問題を保存", type="primary"):
            save(lambda: db.save_question(topic["id"], question, answer, understanding, current.get("id")))


with st.sidebar:
    st.title("Physical AI")
    st.caption("LEARNING NOTEBOOK")
    page = st.radio("ページ", ["ダッシュボード", "トピック", "学習ログ", "理解度チェック"])
    st.divider()
    st.caption("保存は各画面の保存ボタンで行います。データはこのPC内のSQLiteに保存されます。")
    # 個人の学習データをGitHubに含めず、必要なときだけJSONとして取り出す。
    with db.connection() as conn:
        backup = {name: [dict(row) for row in conn.execute(f"SELECT * FROM {name}")]
                  for name in ("topics", "logs", "questions", "artifacts")}
    st.download_button("学習データをJSON出力", json.dumps(backup, ensure_ascii=False, indent=2),
                       file_name=f"physical-ai-{date.today()}.json", mime="application/json")

if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))

topics = db.list_topics()
if page == "ダッシュボード":
    dashboard(topics)
elif page == "トピック":
    topics_page(topics)
elif page == "学習ログ":
    logs_page()
else:
    questions_page(topics)
