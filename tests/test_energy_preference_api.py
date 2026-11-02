"""Energy collection rejects bypasses and preserves explicit private choices."""

import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.main import create_app
import test_accounts_database as database_tests

PATH = "/api/energy-preferences"
BODY = dict(equation_sex="male", activity_category="active", context="general_adult")


class EnergyPreferenceGuardTests(unittest.TestCase):
    def test_identity_and_exact_origin_are_required(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get(PATH).status_code, 401)
            self.assertEqual(client.put(PATH, json=BODY).status_code, 403)
            self.assertEqual(client.put(PATH, json=BODY, headers={"origin": "https://example.invalid"}).status_code, 403)
            self.assertEqual(client.put(PATH, json=BODY, headers={"origin": "http://127.0.0.1"}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class EnergyPreferenceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def setUp(self):
        app = create_app()
        self.first = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.second = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.headers = {"origin": "http://127.0.0.1"}
        for client in (self.first, self.second):
            credentials = dict(username="energyapi_" + uuid4().hex[:16], password="synthetic energy password")
            self.assertEqual(client.post("/auth/register", json=credentials, headers=self.headers).status_code, 201)
            self.assertEqual(client.post("/auth/login", json=credentials, headers=self.headers).status_code, 200)

    def profile(self, client):
        self.assertEqual(client.put("/api/profile", json=dict(age=30, height_cm=175, weight_kg=70, timezone="UTC"),
                                    headers=self.headers).status_code, 200)

    def test_profile_first_and_exact_three_field_response_preserve_uncertainty(self):
        self.assertEqual(self.first.put(PATH, json=BODY, headers=self.headers).status_code, 409)
        self.profile(self.first)
        self.assertEqual(self.first.get(PATH).status_code, 404)
        for body in [BODY, dict(equation_sex="unsure", activity_category="unsure", context="unsure"),
                     BODY | dict(context="pregnant"), BODY | dict(context="clinical")]:
            response = self.first.put(PATH, json=body, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), body)
            self.assertEqual(self.first.get(PATH).json(), body)
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_owner_spoofing_cannot_read_or_change_another_row_and_logout_revokes_access(self):
        for client in (self.first, self.second):
            self.profile(client)
        self.first.put(PATH, json=BODY, headers=self.headers)
        other = self.first.get("/auth/me").json()["user_id"]
        self.assertEqual(self.second.get(PATH, params={"user_id":other}, headers={"X-User-Id":other}).status_code, 404)
        for field, value in [("user_id",other), ("role","admin"), ("method_version","forged"),
                             ("energy_kcal_per_day",500), ("weight_kg",50), ("activity","very_active")]:
            self.assertEqual(self.second.put(PATH, json=BODY | {field:value}, headers=self.headers).status_code, 422)
        changed = BODY | dict(equation_sex="female", activity_category="inactive")
        self.assertEqual(self.second.put(PATH, json=changed, headers=self.headers).json(), changed)
        self.assertEqual(self.first.get(PATH).json(), BODY)
        self.first.post("/auth/logout", headers=self.headers)
        self.assertEqual(self.first.get(PATH).status_code, 401)
        self.assertEqual(self.first.put(PATH, json=BODY, headers=self.headers).status_code, 401)

    def test_invalid_and_missing_choices_preserve_prior_values_without_echo(self):
        self.profile(self.first)
        self.first.put(PATH, json=BODY, headers=self.headers)
        for field in BODY:
            for value in [None, True, 1, [], {}, "private-input-marker", ""]:
                response = self.first.put(PATH, json=BODY | {field:value}, headers=self.headers)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("private-input-marker", response.text)
            missing = dict(BODY)
            del missing[field]
            self.assertEqual(self.first.put(PATH, json=missing, headers=self.headers).status_code, 422)
        self.assertEqual(self.first.get(PATH).json(), BODY)

    def test_oversized_ambiguous_and_nonfinite_json_fail_before_save(self):
        self.profile(self.first)
        headers = self.headers | {"content-type":"application/json"}
        self.assertEqual(self.first.put(PATH, content=b" " * 2049, headers=headers).status_code, 413)
        for raw in ['{"context":"unsure","context":"general_adult"}', '{"activity_category":NaN}']:
            self.assertEqual(self.first.put(PATH, content=raw, headers=headers).status_code, 422)
        self.assertEqual(self.first.get(PATH).status_code, 404)
