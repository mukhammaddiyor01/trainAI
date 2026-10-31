"""Preference ownership, strict HTTP contracts, and request bounds."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests

PATH = "/api/training-preferences"
BODY = dict(experience="beginner", activity="mostly_seated", equipment=["dumbbells"],
            weekdays=[1, 3], session_minutes=30)


class TrainingPreferenceGuardTests(unittest.TestCase):
    def test_anonymous_and_cross_origin_requests_fail_closed(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get(PATH).status_code, 401)
            self.assertEqual(client.put(PATH, json=BODY).status_code, 403)
            self.assertEqual(client.put(PATH, json=BODY, headers={"origin": "https://example.invalid"}).status_code, 403)
            self.assertEqual(client.put(PATH, json=BODY, headers={"origin": "http://127.0.0.1"}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class TrainingPreferenceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def setUp(self):
        app = create_app()
        self.first = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.second = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.headers = {"origin": "http://127.0.0.1"}
        for client in (self.first, self.second):
            credentials = dict(username="prefapi_" + uuid4().hex[:18], password="synthetic preference password")
            self.assertEqual(client.post("/auth/register", json=credentials, headers=self.headers).status_code, 201)
            self.assertEqual(client.post("/auth/login", json=credentials, headers=self.headers).status_code, 200)

    def profile(self, client):
        self.assertEqual(client.put("/api/profile", json=dict(age=30, height_cm=175, weight_kg=70, timezone="UTC"),
                                    headers=self.headers).status_code, 200)

    def test_profile_required_and_responses_expose_only_named_preferences(self):
        self.assertEqual(self.first.put(PATH, json=BODY, headers=self.headers).status_code, 409)
        self.profile(self.first)
        response = self.first.put(PATH, json=BODY, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), BODY)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.first.get(PATH).json(), BODY)

    def test_two_users_and_forged_owner_fields_cannot_share_preferences(self):
        for client in (self.first, self.second):
            self.profile(client)
        self.assertEqual(self.first.put(PATH, json=BODY, headers=self.headers).status_code, 200)
        other = self.first.get("/auth/me").json()["user_id"]
        self.assertEqual(self.second.get(PATH, params={"user_id": other}, headers={"X-User-Id": other}).status_code, 404)
        for key, value in [("user_id", other), ("role", "admin"), ("equipment_mask", 127)]:
            self.assertEqual(self.second.put(PATH, json=BODY | {key: value}, headers=self.headers).status_code, 422)
        changed = BODY | dict(equipment=[], weekdays=[7], session_minutes=20)
        self.assertEqual(self.second.put(PATH, json=changed, headers=self.headers).json(), changed)
        self.assertEqual(self.first.get(PATH).json(), BODY)
        self.first.post("/auth/logout", headers=self.headers)
        self.assertEqual(self.first.get(PATH).status_code, 401)

    def test_invalid_updates_preserve_previous_values_without_echoing_inputs(self):
        self.profile(self.first)
        self.assertEqual(self.first.put(PATH, json=BODY, headers=self.headers).status_code, 200)
        for change in [dict(experience="private-invalid-marker"), dict(activity="unknown"), dict(equipment=["bench", "bench"]),
                       dict(equipment=["unknown"]), dict(weekdays=[1, 1]), dict(weekdays=[]), dict(weekdays=[8]),
                       dict(weekdays=[True]), dict(weekdays=["1"]), dict(session_minutes="30"),
                       dict(session_minutes=True), dict(session_minutes=30.5), dict(session_minutes=181)]:
            response = self.first.put(PATH, json=BODY | change, headers=self.headers)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("private-invalid-marker", response.text)
            self.assertEqual(self.first.get(PATH).json(), BODY)
        missing = dict(BODY)
        del missing["equipment"]
        self.assertEqual(self.first.put(PATH, json=missing, headers=self.headers).status_code, 422)

    def test_oversized_and_ambiguous_json_are_rejected_before_save(self):
        self.profile(self.first)
        headers = self.headers | {"content-type": "application/json"}
        self.assertEqual(self.first.put(PATH, content=b" " * 4097, headers=headers).status_code, 413)
        for raw in ['{"experience":"beginner","experience":"advanced"}', '{"weekdays":[NaN]}']:
            self.assertEqual(self.first.put(PATH, content=raw, headers=headers).status_code, 422)
        self.assertEqual(self.first.get(PATH).status_code, 404)
