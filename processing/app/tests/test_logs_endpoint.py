import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class TestLogsEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_tail_windninja_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "windninja.log")
            with open(log_path, "w", encoding="utf-8") as f:
                for i in range(1, 101):
                    f.write(f"line {i}\n")

            with patch("app.config.settings.LOG_FILE", log_path):
                resp = self.client.get("/logs/windninja", params={"lines": 5})

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers.get("content-type"), "text/plain; charset=utf-8")
            self.assertEqual(resp.text, "".join([f"line {i}\n" for i in range(96, 101)]))

    def test_download_windninja_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "windninja.log")
            content = "hello\nworld\n"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content)

            with patch("app.config.settings.LOG_FILE", log_path):
                resp = self.client.get("/logs/windninja", params={"download": "true"})

            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/plain", resp.headers.get("content-type", ""))
            self.assertEqual(resp.text.replace("\r\n", "\n"), content)


if __name__ == "__main__":
    unittest.main()
