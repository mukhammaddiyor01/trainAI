"""Weekly review API returns bounded owner-only observations."""

from datetime import datetime, timezone
import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class WeightReviewGuardTests(unittest.TestCase):
    def test_anonymous_read_is_rejected(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get("/api/weight-review").status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WeightReviewApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = {"username": "review_api_" + uuid4().hex[:12], "password": "synthetic review password"}
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_profile_first_owner_isolation_and_allowlisted_result(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers, other_headers = self.sign_in(first), self.sign_in(second)
            self.assertEqual(first.get("/api/weight-review").status_code, 404)
            for client, own_headers in ((first, headers), (second, other_headers)):
                self.assertEqual(client.put("/api/profile", json={
                    "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
                }, headers=own_headers).status_code, 200)
            today = datetime.now(timezone.utc).date()
            self.assertEqual(first.put("/api/weight-entries", json={
                "local_date": today.isoformat(), "weight_kg": 71,
            }, headers=headers).status_code, 200)
            response = first.get("/api/weight-review")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.json()), {"weeks"})
            self.assertEqual(len(response.json()["weeks"]), 5)
            self.assertEqual(response.json()["weeks"][0]["observed_dates"], 1)
            self.assertIsNone(response.json()["weeks"][0]["observed_change_kg"])
            self.assertEqual(set(response.json()["weeks"][0]), {
                "week_start", "week_end", "observed_dates", "first", "last", "observed_change_kg",
            })
            self.assertEqual(sum(week["observed_dates"] for week in second.get("/api/weight-review").json()["weeks"]), 0)
            self.assertEqual(first.get("/api/weight-review?user_id=other").status_code, 422)
            self.assertEqual(first.get("/api/weight-review?week_start=2026-01-01").status_code, 422)
