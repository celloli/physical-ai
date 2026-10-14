import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

import database as db


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = db.DB_PATH
        db.DB_PATH = Path(self.temp.name) / "app.db"
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()

    def tearDown(self):
        db.DB_PATH = self.original
        self.temp.cleanup()

    def page(self, name):
        self.app.sidebar.radio[0].set_value(name).run()
        self.assertFalse(self.app.exception)

    def test_dashboard_and_all_pages(self):
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[0].value, "34%")
        for name in ["トピック", "学習ログ", "理解度チェック", "ダッシュボード"]:
            self.page(name)

    def test_create_topic_log_question_and_reload(self):
        self.page("トピック")
        self.app.text_input[1].set_value("テスト用トピック")
        self.app.text_area[1].set_value("小さな実験をする")
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(db.list_topics()), 21)
        self.page("学習ログ")
        self.app.text_area[0].set_value("Attentionを学んだ")
        self.app.button[0].click().run()
        self.assertEqual(db.list_logs()[0]["learned"], "Attentionを学んだ")
        self.page("理解度チェック")
        self.app.text_area[0].set_value("Physical AIとは？")
        self.app.text_area[1].set_value("物理世界で知覚し行動するAI")
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(db.list_questions(1)), 1)

        self.app.run()
        self.assertEqual(len(db.list_topics()), 21)
        self.assertEqual(len(db.list_questions(1)), 1)

    def test_edit_topic_and_add_artifact(self):
        self.page("トピック")
        topic = db.list_topics()[0]
        self.app.selectbox[2].set_value(topic).run()
        self.app.selectbox[4].set_value("実装済み")
        self.app.selectbox[5].set_value(4)
        self.app.text_area[0].set_value("実験した")
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        saved = db.list_topics()[0]
        self.assertEqual(saved["status"], "実装済み")
        self.assertEqual(saved["understanding"], 4)
        # 再選択し、同じIDに成果物が紐づくことを確認する。
        self.app.selectbox[2].set_value(saved).run()
        self.app.text_input[2].set_value("ROS実験")
        self.app.text_input[3].set_value("https://github.com/example/ros")
        self.app.button[1].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(db.list_artifacts(topic["id"])), 1)
