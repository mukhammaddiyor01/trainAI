"""Saved proposal pages keep snapshots private and distinguish pending from approval."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class CalorieProposalPageGuardTests(unittest.TestCase):
    def test_anonymous_redirect(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get(f"/calorie-proposals/{uuid4()}", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CalorieProposalPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = dict(username="proposal_page_" + uuid4().hex[:12], password="synthetic proposal password")
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def test_owner_can_revisit_snapshot_other_owner_cannot(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers = self.sign_in(first)
            self.sign_in(second)
            self.assertEqual(first.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
            }, headers=headers).status_code, 200)
            self.assertEqual(first.put("/api/goal", json={
                "direction": "gain", "target_weight_kg": 75,
            }, headers=headers).status_code, 200)
            self.assertEqual(first.put("/api/energy-preferences", json={
                "equation_sex": "male", "activity_category": "inactive", "context": "general_adult",
            }, headers=headers).status_code, 200)
            created = first.post("/api/calorie-proposals", json={"adjustment_kcal": 200}, headers=headers)
            self.assertEqual(created.status_code, 201)
            path = f"/calorie-proposals/{created.json()['proposal_id']}"
            page = first.get(path)
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.headers["cache-control"], "no-store")
            self.assertIn("Pending review", page.text)
            self.assertIn("has not activated a daily target or plan", page.text)
            self.assertIn('id="approve-proposal"', page.text)
            self.assertIn("+200 kcal/day", page.text)
            self.assertNotIn("synthetic proposal password", page.text)
            self.assertEqual(second.get(path).status_code, 404)
            self.assertEqual(second.get(path + "?user_id=other").status_code, 404)
            self.assertEqual(first.get(f"/calorie-proposals/{uuid4()}").status_code, 404)
            first.post("/auth/logout", headers=headers)
            self.assertEqual(first.get(path, follow_redirects=False).headers["location"], "/login")

    def test_approved_proposal_and_target_history_are_truthful_and_private(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers = self.sign_in(first)
            self.sign_in(second)
            self.assertIn("No approved targets yet", first.get("/calorie-targets").text)
            self.assertEqual(first.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
            }, headers=headers).status_code, 200)
            self.assertEqual(first.put("/api/goal", json={
                "direction": "gain", "target_weight_kg": 75,
            }, headers=headers).status_code, 200)
            self.assertEqual(first.put("/api/energy-preferences", json={
                "equation_sex": "male", "activity_category": "inactive", "context": "general_adult",
            }, headers=headers).status_code, 200)
            proposal_id = first.post("/api/calorie-proposals", json={"adjustment_kcal": 100},
                                     headers=headers).json()["proposal_id"]
            self.assertEqual(first.post(f"/api/calorie-proposals/{proposal_id}/approve",
                                        json={"confirm": True}, headers=headers).status_code, 200)
            page = first.get(f"/calorie-proposals/{proposal_id}")
            self.assertIn("Approved · active target v1", page.text)
            self.assertNotIn('id="approve-proposal"', page.text)
            self.assertIn("Version 1", first.get("/calorie-targets").text)
            self.assertIn("Approved", first.get("/calorie-proposals").text)
            self.assertNotIn(proposal_id, second.get("/calorie-targets").text)
            self.assertEqual(second.get(f"/calorie-proposals/{proposal_id}").status_code, 404)
            first.post("/auth/logout", headers=headers)
            self.assertEqual(first.get("/calorie-targets", follow_redirects=False).headers["location"], "/login")
