"""Food onboarding, escaped reported names, and saved local-clock times."""

import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.main import create_app
import test_accounts_database as database_tests


class FoodPreferencePageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_assets(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            page = client.get("/food-preferences", follow_redirects=False)
            self.assertEqual(page.status_code, 303)
            self.assertEqual(page.headers["location"], "/login")
            for extension in ("css", "js"):
                self.assertEqual(client.get(f"/static/{extension}/food-preferences.{extension}").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class FoodPreferencePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def test_profile_first_saved_values_and_escaped_reported_names(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = {"origin":"http://127.0.0.1"}
            credentials = dict(username="foodpage_" + uuid4().hex[:18], password="synthetic food password")
            self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
            self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
            self.assertEqual(client.get("/food-preferences", follow_redirects=False).headers["location"], "/profile")
            self.assertEqual(client.put("/api/profile", json=dict(age=30, height_cm=175, weight_kg=70, timezone="Asia/Seoul"), headers=headers).status_code, 200)
            empty = client.get("/food-preferences?saved=1")
            self.assertEqual(empty.status_code, 200)
            self.assertNotIn("Food preferences saved.", empty.text)
            body = dict(diet="vegetarian", allergy_status="listed", allergies=['<img src=x onerror=alert(1)>'],
                        budget_level="standard", prep_minutes=15, meal_times=["19:30", "08:00"])
            self.assertEqual(client.put("/api/food-preferences", json=body, headers=headers).status_code, 200)
            page = client.get("/food-preferences?saved=1")
            self.assertIn("Food preferences saved.", page.text)
            self.assertIn('value="vegetarian" selected', page.text)
            self.assertIn('value="listed" selected', page.text)
            self.assertIn('value="15"', page.text)
            self.assertIn('value="08:00"', page.text)
            self.assertIn('value="19:30"', page.text)
            self.assertIn('Asia/Seoul', page.text)
            self.assertIn('&lt;img src=x onerror=alert(1)&gt;', page.text)
            self.assertNotIn('<img src=x', page.text)
