"""Private calorie preview page exposes only explicit, temporary calculation UI."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class CaloriePreviewPageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_assets(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/calorie-preview", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")
            for extension in ("css", "js"):
                self.assertEqual(client.get(f"/static/{extension}/calorie-preview.{extension}").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CaloriePreviewPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def test_prerequisites_explicit_input_and_logout(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = {"origin": "http://127.0.0.1"}
            credentials = dict(username="previewpage_" + uuid4().hex[:14], password="synthetic preview password")
            client.post("/auth/register", json=credentials, headers=headers)
            client.post("/auth/login", json=credentials, headers=headers)
            self.assertEqual(client.get("/calorie-preview", follow_redirects=False).headers["location"], "/profile")
            profile = dict(age=30, height_cm=175, weight_kg=70, timezone="Asia/Seoul")
            client.put("/api/profile", json=profile, headers=headers)
            self.assertNotIn('id="calorie-preview-form"', client.get("/calorie-preview").text)
            client.put("/api/goal", json={"direction": "gain", "target_weight_kg": 75}, headers=headers)
            self.assertNotIn('id="calorie-preview-form"', client.get("/calorie-preview").text)
            client.put("/api/energy-preferences", json={
                "equation_sex": "male", "activity_category": "inactive", "context": "general_adult",
            }, headers=headers)
            page = client.get("/calorie-preview")
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.headers["cache-control"], "no-store")
            self.assertIn('data-direction="gain"', page.text)
            self.assertIn('name="adjustment_kcal"', page.text)
            self.assertNotIn('name="adjustment_kcal" type="number" value=', page.text)
            self.assertIn("No value is chosen for you.", page.text)
            self.assertIn("nothing was saved or activated", page.text)
            self.assertIn('id="save-proposal"', page.text)
            self.assertIn("does not activate a target or plan", page.text)
            self.assertIn("experimental application limits", page.text)
            client.put("/api/goal", json={"direction": "maintain"}, headers=headers)
            self.assertIn('data-direction="maintain"', client.get("/calorie-preview").text)
            client.post("/auth/logout", headers=headers)
            self.assertEqual(client.get("/calorie-preview", follow_redirects=False).headers["location"], "/login")
