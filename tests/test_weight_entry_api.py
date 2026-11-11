"""Weight API rejects forged ownership and returns only bounded owner values."""

from datetime import datetime, timezone
import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class WeightEntryPublicGuardTests(unittest.TestCase):
    def test_anonymous_get_and_write_do_not_expose_records(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get("/api/weight-entries").status_code, 401)
            self.assertEqual(client.put("/api/weight-entries", json={
                "local_date": "2026-11-11", "weight_kg": 70,
            }, headers={"origin": "http://127.0.0.1"}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WeightEntryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = {"username": "weight_api_" + uuid4().hex[:12], "password": "synthetic weight password"}
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_profile_first_owner_isolation_and_response_allowlist(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers = self.sign_in(first)
            other_headers = self.sign_in(second)
            day = datetime.now(timezone.utc).date().isoformat()
            payload = {"local_date": day, "weight_kg": 71.25}
            self.assertEqual(first.get("/api/weight-entries").json(), {"items": []})
            self.assertEqual(first.put("/api/weight-entries", json=payload, headers=headers).status_code, 409)
            for client, own_headers in ((first, headers), (second, other_headers)):
                self.assertEqual(client.put("/api/profile", json={
                    "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
                }, headers=own_headers).status_code, 200)
            saved = first.put("/api/weight-entries", json=payload, headers=headers)
            self.assertEqual(saved.status_code, 200)
            self.assertEqual(saved.json(), payload)
            self.assertEqual(first.get("/api/weight-entries").json(), {"items": [payload]})
            self.assertEqual(second.get("/api/weight-entries").json(), {"items": []})
            self.assertEqual(first.get("/api/profile").json()["weight_kg"], 70)

    def test_strict_input_origin_query_and_invalid_updates(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = self.sign_in(client)
            self.assertEqual(client.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
            }, headers=headers).status_code, 200)
            day = datetime.now(timezone.utc).date().isoformat()
            good = {"local_date": day, "weight_kg": 70.5}
            self.assertEqual(client.put("/api/weight-entries", json=good, headers=headers).status_code, 200)
            self.assertEqual(client.put("/api/weight-entries", json=good).status_code, 403)
            self.assertEqual(client.put("/api/weight-entries", json=good,
                                        headers={"origin": "http://evil.example"}).status_code, 403)
            for bad in ({**good, "user_id": str(uuid4())},
                        {**good, "local_date": "9999-12-31"},
                        {**good, "local_date": "2026-02-30"},
                        {**good, "weight_kg": "70.5"},
                        {**good, "weight_kg": True},
                        {**good, "weight_kg": 501}):
                with self.subTest(bad=bad):
                    self.assertEqual(client.put("/api/weight-entries", json=bad, headers=headers).status_code, 422)
            self.assertEqual(client.put("/api/weight-entries?user_id=other", json=good,
                                        headers=headers).status_code, 422)
            self.assertEqual(client.get("/api/weight-entries?user_id=other").status_code, 422)
            self.assertEqual(client.get("/api/weight-entries").json(), {"items": [good]})
            self.assertEqual(client.put("/api/weight-entries", content=b'{"local_date":"' + day.encode() +
                                        b'","weight_kg":70,"weight_kg":71}', headers={**headers,
                                        "content-type": "application/json"}).status_code, 422)
            self.assertEqual(client.put("/api/weight-entries", content=b"{" + b" " * 2100 + b"}",
                                        headers={**headers, "content-type": "application/json"}).status_code, 413)
