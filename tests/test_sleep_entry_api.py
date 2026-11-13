"""Sleep API rejects forged ownership and returns only bounded owner values."""

from datetime import datetime, timezone
import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class SleepEntryGuardTests(unittest.TestCase):
    def test_anonymous_get_and_write_are_rejected(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get("/api/sleep-entries").status_code, 401)
            self.assertEqual(client.put("/api/sleep-entries", json={
                "local_date": "2026-11-13", "sleep_minutes": 450,
            }, headers={"origin": "http://127.0.0.1"}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class SleepEntryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = {"username": "sleep_api_" + uuid4().hex[:12], "password": "synthetic sleep password"}
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_profile_first_owner_isolation_and_zero_value(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers, other_headers = self.sign_in(first), self.sign_in(second)
            day = datetime.now(timezone.utc).date().isoformat()
            payload = {"local_date": day, "sleep_minutes": 450}
            self.assertEqual(first.get("/api/sleep-entries").json(), {"items": []})
            self.assertEqual(first.put("/api/sleep-entries", json=payload, headers=headers).status_code, 409)
            for client, own_headers in ((first, headers), (second, other_headers)):
                self.assertEqual(client.put("/api/profile", json={
                    "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
                }, headers=own_headers).status_code, 200)
            self.assertEqual(first.put("/api/sleep-entries", json=payload, headers=headers).json(), payload)
            corrected = {**payload, "sleep_minutes": 0}
            self.assertEqual(first.put("/api/sleep-entries", json=corrected, headers=headers).json(), corrected)
            self.assertEqual(first.get("/api/sleep-entries").json(), {"items": [corrected]})
            self.assertEqual(second.get("/api/sleep-entries").json(), {"items": []})
            self.assertEqual(first.get("/api/profile").json()["weight_kg"], 70)

    def test_strict_input_origin_query_and_invalid_update(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = self.sign_in(client)
            self.assertEqual(client.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
            }, headers=headers).status_code, 200)
            good = {"local_date": datetime.now(timezone.utc).date().isoformat(), "sleep_minutes": 450}
            self.assertEqual(client.put("/api/sleep-entries", json=good, headers=headers).status_code, 200)
            self.assertEqual(client.put("/api/sleep-entries", json=good).status_code, 403)
            self.assertEqual(client.put("/api/sleep-entries", json=good,
                                        headers={"origin": "http://evil.example"}).status_code, 403)
            for bad in ({**good, "user_id": str(uuid4())}, {**good, "local_date": "9999-12-31"},
                        {**good, "local_date": "2026-02-30"}, {**good, "sleep_minutes": "450"},
                        {**good, "sleep_minutes": True}, {**good, "sleep_minutes": -1},
                        {**good, "sleep_minutes": 1441}):
                with self.subTest(bad=bad):
                    self.assertEqual(client.put("/api/sleep-entries", json=bad, headers=headers).status_code, 422)
            self.assertEqual(client.put("/api/sleep-entries?user_id=other", json=good,
                                        headers=headers).status_code, 422)
            self.assertEqual(client.get("/api/sleep-entries?user_id=other").status_code, 422)
            self.assertEqual(client.put("/api/sleep-entries", content=b'{"local_date":"' + good["local_date"].encode() +
                                        b'","sleep_minutes":420,"sleep_minutes":450}',
                                        headers={**headers, "content-type": "application/json"}).status_code, 422)
            self.assertEqual(client.put("/api/sleep-entries", content=b"{" + b" " * 2100 + b"}",
                                        headers={**headers, "content-type": "application/json"}).status_code, 413)
            self.assertEqual(client.get("/api/sleep-entries").json(), {"items": [good]})
