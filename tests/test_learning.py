import tempfile
import unittest
from datetime import date
from pathlib import Path

import database as db
from learning import progress, today_tasks


class LearningTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = db.DB_PATH
        db.DB_PATH = Path(self.temp.name) / "learning.db"
        db.initialize()

    def tearDown(self):
        db.DB_PATH = self.original
        self.temp.cleanup()

    def test_seed_is_idempotent_and_preserves_edits(self):
        topics = db.list_topics()
        self.assertEqual(len(topics), 20)
        self.assertEqual(progress(topics), 34)
        self.assertEqual(sum(t["status"] == "完了" for t in topics), 4)
        db.save_topic(topics[0]["field"], "変更済み", "学習中", 2, "メモ", "次", topics[0]["id"])
        db.initialize()
        self.assertEqual(len(db.list_topics()), 20)
        self.assertEqual(db.list_topics()[0]["name"], "変更済み")

    def test_recommendations_and_empty_data(self):
        tasks = today_tasks(db.list_topics())
        self.assertEqual(len(tasks), 3)
        self.assertTrue(all(t["status"] == "学習中" for t, _ in tasks))
        self.assertEqual(progress([]), 0)
        self.assertEqual(today_tasks([]), [])
        self.assertEqual(today_tasks([t for t in db.list_topics() if t["status"] == "完了"]), [])

    def test_logs_update_without_duplicate(self):
        day = date(2026, 10, 14)
        db.save_log(day, "Attention", "", "", "")
        db.save_log(day, "Attention", "実装", "疑問", "復習")
        self.assertEqual(len(db.list_logs()), 1)
        self.assertEqual(db.list_logs()[0]["practiced"], "実装")

    def test_related_records_survive_rename(self):
        topic = db.list_topics()[0]
        topic_id = topic["id"]
        db.save_question(topic_id, "Physical AIとは？", "回答", 3)
        question = db.list_questions(topic_id)[0]
        db.save_question(topic_id, "Physical AIとは？", "更新回答", 4, question["id"])
        db.save_artifact(topic_id, "ROS実験", "https://github.com/example/ros")
        db.save_topic(topic["field"], "変更", "概念理解", 4, "", "実験", topic_id)
        self.assertEqual(db.list_questions(topic_id)[0]["answer"], "更新回答")
        self.assertEqual(len(db.list_questions(topic_id)), 1)
        self.assertEqual(len(db.list_artifacts(topic_id)), 1)

    def test_validation(self):
        with self.assertRaises(ValueError):
            db.save_topic("ROS 2", "  ", "学習中", 3, "", "")
        with self.assertRaises(ValueError):
            db.save_log(date.today(), "", "", "", "")
        with self.assertRaises(ValueError):
            db.save_question(1, " ", "", 1)
