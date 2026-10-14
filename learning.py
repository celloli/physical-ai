"""画面やデータベースから独立した学習ルール。"""

STATUS_PROGRESS = {"未学習": 0, "学習中": 25, "概念理解": 50, "実装済み": 75, "完了": 100}
FIELDS = [
    "Physical AI 基礎編", "Physical AI 応用編", "Deep Learning", "ROS 2",
    "VLA", "World Model", "Robot Learning", "Reinforcement Learning", "Git / GitHub / Docker",
]


def progress(topics):
    """完了率ではなく、状態に応じた到達度の平均を返す。"""
    return round(sum(STATUS_PROGRESS[t["status"]] for t in topics) / len(topics)) if topics else 0


def today_tasks(topics):
    """学習中→概念理解→実装済み→未学習の順。登録順で安定させる。"""
    priority = {"学習中": 0, "概念理解": 1, "実装済み": 2, "未学習": 3}
    candidates = sorted(
        (t for t in topics if t["status"] != "完了"),
        key=lambda t: (priority[t["status"]], t["id"]),
    )
    fallback = {
        "未学習": "教材を開いて概要を読み、学習中に変更する",
        "学習中": "要点を3つメモし、小さなコードや図で確かめる",
        "概念理解": "最小の実装・実験を1つ試す",
        "実装済み": "動作結果を確認し、学習内容を自分の言葉で説明する",
    }
    return [(t, t["next_action"].strip() or fallback[t["status"]]) for t in candidates[:3]]
