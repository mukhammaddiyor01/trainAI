"""Private weight-log page shows owner records and local-date context."""

from datetime import datetime, timezone
import os
import unittest
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class WeightEntryPageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_assets(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/weight-log", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")
            for asset in ("css", "js"):
                self.assertEqual(client.get(f"/static/{asset}/weight-log.{asset}").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WeightEntryPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = {"username": "weight_page_" + uuid4().hex[:12], "password": "synthetic page password"}
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_profile_first_saved_entry_and_owner_isolation(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers = self.sign_in(first)
            other_headers = self.sign_in(second)
            self.assertEqual(first.get("/weight-log", follow_redirects=False).headers["location"], "/profile")
            self.assertEqual(first.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "Asia/Seoul",
            }, headers=headers).status_code, 200)
            self.assertEqual(second.put("/api/profile", json={
                "age": 32, "height_cm": 170, "weight_kg": 80, "timezone": "UTC",
            }, headers=other_headers).status_code, 200)
            today = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
            empty = first.get("/weight-log")
            self.assertEqual(empty.status_code, 200)
            self.assertIn(f'max="{today}"', empty.text)
            self.assertIn("No observations yet.", empty.text)
            self.assertNotIn("Observation saved.", empty.text)
            self.assertEqual(first.put("/api/weight-entries", json={
                "local_date": today, "weight_kg": 71.25,
            }, headers=headers).status_code, 200)
            saved = first.get("/weight-log?saved=1&user_id=forged")
            self.assertIn("Observation saved.", saved.text)
            self.assertIn("71.25 kg", saved.text)
            self.assertIn(f'data-date="{today}"', saved.text)
            self.assertNotIn("No observations yet.", saved.text)
            other = second.get("/weight-log?saved=1&user_id=forged")
            self.assertIn("No observations yet.", other.text)
            self.assertNotIn("71.25 kg", other.text)
