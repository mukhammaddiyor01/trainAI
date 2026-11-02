"""Private energy onboarding renders truthful empty, uncertain, and calculated states."""

import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.main import create_app
import test_accounts_database as database_tests


class EnergyPreferencePageGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_assets(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/energy-preferences", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login")
            for extension in ("css", "js"):
                self.assertEqual(client.get(f"/static/{extension}/energy-preferences.{extension}").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class EnergyPreferencePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def test_profile_first_explicit_choices_estimate_and_current_profile_reload(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = {"origin":"http://127.0.0.1"}
            credentials = dict(username="energypage_" + uuid4().hex[:14], password="synthetic energy password")
            client.post("/auth/register", json=credentials, headers=headers)
            client.post("/auth/login", json=credentials, headers=headers)
            self.assertEqual(client.get("/energy-preferences", follow_redirects=False).headers["location"], "/profile")
            profile = dict(age=30, height_cm=175, weight_kg=70, timezone="Asia/Seoul")
            client.put("/api/profile", json=profile, headers=headers)
            empty = client.get("/energy-preferences?saved=1")
            self.assertEqual(empty.status_code, 200)
            self.assertNotIn("Energy preferences saved.", empty.text)
            self.assertNotIn('class="energy-value"', empty.text)
            self.assertEqual(empty.text.count('disabled selected'), 3)
            self.assertIn('method="post"', empty.text)
            body = dict(equation_sex="male", activity_category="active", context="general_adult")
            client.put("/api/energy-preferences", json=body, headers=headers)
            page = client.get("/energy-preferences?saved=1")
            self.assertIn("Energy preferences saved.", page.text)
            self.assertIn('value="male" selected', page.text)
            self.assertIn('value="active" selected', page.text)
            self.assertIn('value="general_adult" selected', page.text)
            self.assertIn("About 2,935", page.text)
            self.assertIn("dri-2023-adult-eer-v1", page.text)
            self.assertEqual(page.headers["cache-control"], "no-store")
            client.put("/api/profile", json=profile | dict(weight_kg=80), headers=headers)
            self.assertIn("About 3,094", client.get("/energy-preferences").text)
            for change in [dict(equation_sex="unsure"), dict(context="pregnant"), dict(context="clinical")]:
                client.put("/api/energy-preferences", json=body | change, headers=headers)
                self.assertNotIn('class="energy-value"', client.get("/energy-preferences").text)
            client.post("/auth/logout", headers=headers)
            self.assertEqual(client.get("/energy-preferences", follow_redirects=False).headers["location"], "/login")
