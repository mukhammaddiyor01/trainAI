"""The sleep page shows owner-only dates, duration, and honest empty state."""

from datetime import datetime, timezone
import os
import unittest
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class SleepEntryPageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_assets(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/sleep-log", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")
            for asset in ("css", "js"):
                self.assertEqual(client.get(f"/static/{asset}/sleep-log.{asset}").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class SleepEntryPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = {"username": "sleep_page_" + uuid4().hex[:12], "password": "synthetic sleep password"}
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_profile_first_saved_entry_and_owner_isolation(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers, other_headers = self.sign_in(first), self.sign_in(second)
            self.assertEqual(first.get("/sleep-log", follow_redirects=False).headers["location"], "/profile")
            self.assertEqual(first.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "Asia/Seoul",
            }, headers=headers).status_code, 200)
            self.assertEqual(second.put("/api/profile", json={
                "age": 32, "height_cm": 170, "weight_kg": 80, "timezone": "UTC",
            }, headers=other_headers).status_code, 200)
            today = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
            empty = first.get("/sleep-log")
            self.assertEqual(empty.status_code, 200)
            self.assertIn(f'max="{today}"', empty.text)
            self.assertIn("No sleep observations yet.", empty.text)
            self.assertNotIn("Sleep observation saved.", empty.text)
            self.assertEqual(first.put("/api/sleep-entries", json={
                "local_date": today, "sleep_minutes": 0,
            }, headers=headers).status_code, 200)
            saved = first.get("/sleep-log?saved=1&user_id=forged")
            self.assertIn("Sleep observation saved.", saved.text)
            self.assertIn("0h 00m", saved.text)
            self.assertIn(f'data-date="{today}"', saved.text)
            self.assertIn('data-minutes="0"', saved.text)
            self.assertNotIn("No sleep observations yet.", saved.text)
            other = second.get("/sleep-log?saved=1&user_id=forged")
            self.assertIn("No sleep observations yet.", other.text)
            self.assertNotIn('data-minutes="0"', other.text)
