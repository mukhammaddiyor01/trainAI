"""Private movement answer page renders explicit empty and saved states."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class MovementLimitationPageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_assets(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/movement-limitations", follow_redirects=False)
            self.assertEqual((response.status_code, response.headers["location"]), (303, "/login"))
            for asset in ("/static/js/movement-limitations.js", "/static/css/movement-limitations.css"):
                self.assertEqual(client.get(asset).status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class MovementLimitationPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def test_profile_first_and_answer_reload(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = {"origin": "http://127.0.0.1"}
            credentials = dict(username="movement_page_" + uuid4().hex[:12], password="synthetic movement password")
            self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
            self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
            self.assertEqual(client.get("/movement-limitations", follow_redirects=False).headers["location"], "/profile")
            self.assertEqual(client.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
            }, headers=headers).status_code, 200)
            empty = client.get("/movement-limitations?saved=1")
            self.assertEqual(empty.status_code, 200)
            self.assertNotIn(' checked', empty.text)
            self.assertNotIn("Movement limitation answer saved.", empty.text)
            self.assertIn("not medical clearance", empty.text)
            self.assertIn('href="/movement-limitations"', client.get("/account").text)
            self.assertEqual(client.put("/api/movement-limitations", json={
                "status": "needs_adaptation",
            }, headers=headers).status_code, 200)
            page = client.get("/movement-limitations?saved=1")
            self.assertIn('value="needs_adaptation" checked', page.text)
            self.assertIn("Movement limitation answer saved.", page.text)
            self.assertEqual(page.headers["cache-control"], "no-store")
            client.post("/auth/logout", headers=headers)
            self.assertEqual(client.get("/movement-limitations", follow_redirects=False).headers["location"], "/login")
