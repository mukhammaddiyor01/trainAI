"""Food-preference API identity guards, privacy, strict types, and resource limits."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from backend.main import create_app
import test_accounts_database as database_tests

PATH = "/api/food-preferences"
BODY = dict(diet="mixed", allergy_status="unsure", allergies=[], budget_level="economical",
            prep_minutes=20, meal_times=["08:00", "19:30"])


class FoodPreferenceGuardTests(unittest.TestCase):
    def test_identity_and_exact_origin_are_required(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get(PATH).status_code, 401)
            self.assertEqual(client.put(PATH, json=BODY).status_code, 403)
            self.assertEqual(client.put(PATH, json=BODY, headers={"origin": "https://example.invalid"}).status_code, 403)
            self.assertEqual(client.put(PATH, json=BODY, headers={"origin": "http://127.0.0.1"}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class FoodPreferenceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def setUp(self):
        app = create_app()
        self.first = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.second = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.headers = {"origin": "http://127.0.0.1"}
        for client in (self.first, self.second):
            credentials = dict(username="foodapi_" + uuid4().hex[:18], password="synthetic food password")
            self.assertEqual(client.post("/auth/register", json=credentials, headers=self.headers).status_code, 201)
            self.assertEqual(client.post("/auth/login", json=credentials, headers=self.headers).status_code, 200)

    def profile(self, client):
        self.assertEqual(client.put("/api/profile", json=dict(age=30, height_cm=175, weight_kg=70, timezone="UTC"),
                                    headers=self.headers).status_code, 200)

    def test_profile_required_and_canonical_response_has_only_six_fields(self):
        self.assertEqual(self.first.put(PATH, json=BODY, headers=self.headers).status_code, 409)
        self.profile(self.first)
        body = BODY | dict(allergy_status="listed", allergies=[" Sesame ", "Milk"], meal_times=["19:30", "08:00"])
        response = self.first.put(PATH, json=body, headers=self.headers)
        expected = body | dict(allergies=["milk", "sesame"], meal_times=["08:00", "19:30"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        self.assertEqual(self.first.get(PATH).json(), expected)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_owner_spoofing_cannot_read_or_overwrite_other_preferences(self):
        for client in (self.first, self.second):
            self.profile(client)
        self.assertEqual(self.first.put(PATH, json=BODY, headers=self.headers).status_code, 200)
        other = self.first.get("/auth/me").json()["user_id"]
        self.assertEqual(self.second.get(PATH, params={"user_id":other}, headers={"X-User-Id":other}).status_code, 404)
        for field, value in [("user_id", other), ("role", "admin"), ("meal_minutes", [480]), ("timezone", "UTC")]:
            self.assertEqual(self.second.put(PATH, json=BODY | {field:value}, headers=self.headers).status_code, 422)
        changed = BODY | dict(diet="vegan", allergy_status="none_reported", prep_minutes=0)
        self.assertEqual(self.second.put(PATH, json=changed, headers=self.headers).json(), changed)
        self.assertEqual(self.first.get(PATH).json(), BODY)
        self.first.post("/auth/logout", headers=self.headers)
        self.assertEqual(self.first.get(PATH).status_code, 401)

    def test_invalid_updates_preserve_stored_values_and_do_not_echo_private_text(self):
        self.profile(self.first)
        self.first.put(PATH, json=BODY, headers=self.headers)
        for change in [dict(diet="invalid-private-marker"), dict(allergy_status="listed"), dict(allergies=["milk"]),
                       dict(allergy_status="none_reported", allergies=["milk"]),
                       dict(allergy_status="listed", allergies=["Milk", " milk "]),
                       dict(allergy_status="listed", allergies=["private-allergy\n"]),
                       dict(prep_minutes=True), dict(prep_minutes="20"), dict(prep_minutes=20.5),
                       dict(prep_minutes=181), dict(meal_times=[]), dict(meal_times=["24:00"]),
                       dict(meal_times=["08:00", "08:00"]), dict(meal_times=[800]), dict(budget_level=100)]:
            response = self.first.put(PATH, json=BODY | change, headers=self.headers)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("invalid-private-marker", response.text)
            self.assertNotIn("private-allergy", response.text)
        missing = dict(BODY)
        del missing["allergy_status"]
        self.assertEqual(self.first.put(PATH, json=missing, headers=self.headers).status_code, 422)
        self.assertEqual(self.first.get(PATH).json(), BODY)

    def test_oversized_duplicate_and_nonfinite_json_fail_before_save(self):
        self.profile(self.first)
        headers = self.headers | {"content-type":"application/json"}
        self.assertEqual(self.first.put(PATH, content=b" " * 8193, headers=headers).status_code, 413)
        for raw in ['{"diet":"mixed","diet":"vegan"}', '{"prep_minutes":NaN}']:
            self.assertEqual(self.first.put(PATH, content=raw, headers=headers).status_code, 422)
        self.assertEqual(self.first.get(PATH).status_code, 404)
