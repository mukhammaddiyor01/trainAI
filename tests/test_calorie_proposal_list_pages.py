"""Private proposal list discovers bounded owner snapshots without approval."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class ProposalListPublicGuardTests(unittest.TestCase):
    def test_anonymous_redirect(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/calorie-proposals", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class ProposalListPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = dict(username="proposal_list_" + uuid4().hex[:12], password="synthetic proposal password")
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_empty_list_and_owner_only_paged_links(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers = self.sign_in(first)
            self.sign_in(second)
            empty = first.get("/calorie-proposals")
            self.assertEqual(empty.status_code, 200)
            self.assertIn("No proposals here yet.", empty.text)
            self.assertIn("Create a preview", empty.text)
            first.put("/api/profile", json={"age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC"}, headers=headers)
            first.put("/api/goal", json={"direction": "gain", "target_weight_kg": 75}, headers=headers)
            first.put("/api/energy-preferences", json={
                "equation_sex": "male", "activity_category": "inactive", "context": "general_adult",
            }, headers=headers)
            ids = [first.post("/api/calorie-proposals", json={"adjustment_kcal": 100},
                              headers=headers).json()["proposal_id"] for _ in range(22)]
            latest = first.get("/calorie-proposals")
            self.assertEqual(latest.status_code, 200)
            self.assertEqual(latest.headers["cache-control"], "no-store")
            self.assertIn(ids[-1], latest.text)
            self.assertNotIn(ids[0], latest.text)
            self.assertIn("View older proposals", latest.text)
            cursor = ids[2]
            older = first.get(f"/calorie-proposals?before={cursor}")
            self.assertEqual(older.status_code, 200)
            self.assertIn(ids[0], older.text)
            self.assertNotIn(ids[-1], older.text)
            self.assertNotIn("View older proposals", older.text)
            self.assertEqual(second.get("/calorie-proposals").status_code, 200)
            self.assertNotIn(ids[-1], second.get("/calorie-proposals").text)
            self.assertEqual(second.get(f"/calorie-proposals?before={cursor}").status_code, 404)
            self.assertEqual(first.get("/calorie-proposals?before=bad").status_code, 404)
            self.assertEqual(first.get("/calorie-proposals?user_id=other").status_code, 404)
            self.assertIn('href="/calorie-proposals"', first.get("/account").text)
