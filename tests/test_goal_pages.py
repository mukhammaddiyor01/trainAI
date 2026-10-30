"""Authenticated goal pages, onboarding order, and saved values."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class GoalPageGuardTests(unittest.TestCase):
    def test_anonymous_goal_page_redirects_and_local_assets_load(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/goal", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")
            for path in ["/static/css/goal.css", "/static/js/goal.js"]:
                self.assertEqual(client.get(path).status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class GoalPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def test_profile_precedes_goal_and_saved_goal_values_are_rendered(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = {"origin": "http://127.0.0.1"}
            values = {"username": "goalpage_" + uuid4().hex[:18], "password": "synthetic goal passphrase"}
            self.assertEqual(client.post("/auth/register", headers=headers, json=values).status_code, 201)
            self.assertEqual(client.post("/auth/login", headers=headers, json=values).status_code, 200)
            response = client.get("/goal", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/profile")
            self.assertEqual(client.put("/api/profile", headers=headers,
                                       json={"age": 30, "height_cm": 175.0, "weight_kg": 60.0, "timezone": "UTC"}).status_code, 200)
            self.assertEqual(client.get("/goal").status_code, 200)
            self.assertEqual(client.put("/api/goal", headers=headers,
                                       json={"direction": "gain", "target_weight_kg": 75.0}).status_code, 200)
            page = client.get("/goal?saved=1")
            self.assertIn('value="75.0"', page.text)
            self.assertIn('value="gain" selected', page.text)
            self.assertIn('Goal starting weight', page.text)
            self.assertIn('Goal saved.', page.text)
