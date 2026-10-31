"""Preference page onboarding, saved selections, and local asset availability."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class TrainingPreferencePageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_assets(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/training-preferences", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")
            for asset in ("css", "js"):
                self.assertEqual(client.get(f"/static/{asset}/training-preferences.{asset}").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class TrainingPreferencePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def test_profile_first_and_saved_selections_are_rendered(self):
        from html.parser import HTMLParser
        class Inputs(HTMLParser):
            def __init__(self, html):
                super().__init__()
                self.checked = []
                self.feed(html)
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if tag == "input" and "checked" in values:
                    self.checked.append((values["name"], values["value"]))
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = {"origin": "http://127.0.0.1"}
            credentials = dict(username="prefpage_" + uuid4().hex[:18], password="synthetic preference password")
            self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
            self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
            response = client.get("/training-preferences", follow_redirects=False)
            self.assertEqual(response.headers["location"], "/profile")
            self.assertEqual(client.put("/api/profile", json=dict(age=30, height_cm=175, weight_kg=70, timezone="UTC"), headers=headers).status_code, 200)
            empty = client.get("/training-preferences?saved=1")
            self.assertEqual(empty.status_code, 200)
            self.assertNotIn("Training preferences saved.", empty.text)
            self.assertEqual(Inputs(empty.text).checked, [])
            body = dict(experience="intermediate", activity="lightly_active", weekdays=[7, 1], equipment=["bench"], session_minutes=45)
            self.assertEqual(client.put("/api/training-preferences", json=body, headers=headers).status_code, 200)
            page = client.get("/training-preferences?saved=1")
            self.assertIn("Training preferences saved.", page.text)
            self.assertIn('value="45"', page.text)
            self.assertIn('value="intermediate" selected', page.text)
            self.assertIn('value="lightly_active" selected', page.text)
            self.assertEqual(Inputs(page.text).checked, [("weekdays", "1"), ("weekdays", "7"), ("equipment", "bench")])
