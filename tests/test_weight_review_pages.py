"""The review page renders owner-only evidence and honest empty weeks."""

from datetime import datetime, timedelta, timezone
import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class WeightReviewPageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_style(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/weight-review", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")
            self.assertEqual(client.get("/static/css/weight-review.css").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WeightReviewPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = {"username": "review_page_" + uuid4().hex[:12], "password": "synthetic review password"}
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_profile_first_empty_single_and_two_date_owner_states(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers, other_headers = self.sign_in(first), self.sign_in(second)
            self.assertEqual(first.get("/weight-review", follow_redirects=False).headers["location"], "/profile")
            for client, own_headers in ((first, headers), (second, other_headers)):
                self.assertEqual(client.put("/api/profile", json={
                    "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
                }, headers=own_headers).status_code, 200)
            empty = first.get("/weight-review")
            self.assertEqual(empty.status_code, 200)
            self.assertEqual(empty.text.count("No observations recorded for this week."), 5)
            self.assertIn("no-store", empty.headers["cache-control"])
            today = datetime.now(timezone.utc).date()
            last_monday = today - timedelta(days=today.weekday() + 7)
            for day, weight in ((last_monday, 71), (last_monday + timedelta(days=1), 70.5)):
                self.assertEqual(first.put("/api/weight-entries", json={
                    "local_date": day.isoformat(), "weight_kg": weight,
                }, headers=headers).status_code, 200)
            page = first.get("/weight-review?user_id=forged")
            self.assertIn("-0.5 kg", page.text)
            self.assertIn("Observed change", page.text)
            self.assertEqual(page.text.count("No observations recorded for this week."), 4)
            self.assertNotIn("-0.5 kg", second.get("/weight-review?user_id=forged").text)
