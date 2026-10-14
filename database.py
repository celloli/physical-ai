"""SQLiteの保存処理。UIを変えても、このファイルは再利用できる。"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from learning import STATUS_PROGRESS
from seed_data import INITIAL_TOPICS

DB_PATH = Path(os.environ.get("PHYSICAL_AI_DB", Path(__file__).parent / "data" / "learning.db"))


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:  # 成功時に確定し、失敗時には取り消す。
            yield conn
    finally:
        conn.close()


def initialize():
    with connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY, field TEXT NOT NULL, name TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('未学習','学習中','概念理解','実装済み','完了')),
                understanding INTEGER CHECK(understanding BETWEEN 1 AND 5),
                notes TEXT NOT NULL DEFAULT '', next_action TEXT NOT NULL DEFAULT '',
                UNIQUE(field, name)
            );
            CREATE TABLE IF NOT EXISTS logs (
                day TEXT PRIMARY KEY, learned TEXT NOT NULL, practiced TEXT NOT NULL,
                unclear TEXT NOT NULL, next_action TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL REFERENCES topics(id),
                question TEXT NOT NULL, answer TEXT NOT NULL,
                understanding INTEGER NOT NULL CHECK(understanding BETWEEN 1 AND 5)
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL REFERENCES topics(id),
                label TEXT NOT NULL, location TEXT NOT NULL, UNIQUE(topic_id, location)
            );
        """)
        # 空かどうかではなく初期化マーカーで判定し、再起動時の重複を防ぐ。
        if not conn.execute("SELECT 1 FROM metadata WHERE key = 'seeded'").fetchone():
            for field, topics in INITIAL_TOPICS.items():
                conn.executemany(
                    "INSERT OR IGNORE INTO topics(field,name,status,notes) VALUES (?,?,?,?)",
                    [(field, name, status, notes) for name, status, notes in topics],
                )
            conn.execute("INSERT INTO metadata VALUES ('seeded', '1')")


def list_topics():
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM topics ORDER BY id")]


def save_topic(field, name, status, understanding, notes, next_action, topic_id=None):
    field, name = field.strip(), name.strip()
    if not field or not name:
        raise ValueError("分野とトピック名を入力してください。")
    if status not in STATUS_PROGRESS:
        raise ValueError("状態を選び直してください。")
    if understanding is not None and understanding not in range(1, 6):
        raise ValueError("理解度は1〜5で指定してください。")
    values = (field, name, status, understanding, notes.strip(), next_action.strip())
    with connection() as conn:
        if topic_id is None:
            conn.execute("INSERT INTO topics(field,name,status,understanding,notes,next_action) VALUES (?,?,?,?,?,?)", values)
        else:
            conn.execute("UPDATE topics SET field=?,name=?,status=?,understanding=?,notes=?,next_action=? WHERE id=?", (*values, topic_id))


def list_logs():
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM logs ORDER BY day DESC")]


def save_log(day, learned, practiced, unclear, next_action):
    if not any(v.strip() for v in (learned, practiced, unclear, next_action)):
        raise ValueError("ログの項目を1つ以上入力してください。")
    with connection() as conn:
        conn.execute("""INSERT INTO logs VALUES (?,?,?,?,?) ON CONFLICT(day) DO UPDATE SET
            learned=excluded.learned, practiced=excluded.practiced,
            unclear=excluded.unclear, next_action=excluded.next_action""",
            (day.isoformat(), learned.strip(), practiced.strip(), unclear.strip(), next_action.strip()))


def list_questions(topic_id):
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM questions WHERE topic_id=? ORDER BY id", (topic_id,))]


def save_question(topic_id, question, answer, understanding, question_id=None):
    if not question.strip():
        raise ValueError("確認問題を入力してください。")
    with connection() as conn:
        if question_id is None:
            conn.execute("INSERT INTO questions(topic_id,question,answer,understanding) VALUES (?,?,?,?)",
                         (topic_id, question.strip(), answer.strip(), understanding))
        else:
            conn.execute("UPDATE questions SET question=?,answer=?,understanding=? WHERE id=? AND topic_id=?",
                         (question.strip(), answer.strip(), understanding, question_id, topic_id))


def list_artifacts(topic_id):
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM artifacts WHERE topic_id=? ORDER BY id", (topic_id,))]


def save_artifact(topic_id, label, location):
    if not label.strip() or not location.strip():
        raise ValueError("成果物の名前とURLまたはパスを入力してください。")
    with connection() as conn:
        conn.execute("INSERT INTO artifacts(topic_id,label,location) VALUES (?,?,?)",
                     (topic_id, label.strip(), location.strip()))
