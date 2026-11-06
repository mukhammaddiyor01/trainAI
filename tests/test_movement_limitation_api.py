"""Movement self-report API preserves unknown status and account boundaries."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests

PATH = "/api/movement-limitations"
ORIGIN = {"origin": "http://127.0.0.1"}


class MovementLimitationGuardTests(unittest.TestCase):
    def test_origin_and_identity_are_required(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get(PATH).status_code, 401)
            self.assertEqual(client.put(PATH, json={"status": "unsure"}).status_code, 403)
            self.assertEqual(client.put(PATH, json={"status": "unsure"}, headers=ORIGIN).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class MovementLimitationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        credentials = dict(username="movement_api_" + uuid4().hex[:12], password="synthetic movement password")
        self.assertEqual(client.post("/auth/register", json=credentials, headers=ORIGIN).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=ORIGIN).status_code, 200)
        return client.get("/auth/me").json()["user_id"]

    def profile(self, client):
        self.assertEqual(client.put("/api/profile", json={
            "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
        }, headers=ORIGIN).status_code, 200)

    def test_explicit_choices_are_private_and_profile_first(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            first_id, second_id = self.sign_in(first), self.sign_in(second)
            self.assertNotEqual(first_id, second_id)
            self.assertEqual(first.get(PATH).status_code, 404)
            self.assertEqual(first.put(PATH, json={"status": "unsure"}, headers=ORIGIN).status_code, 409)
            self.profile(first)
            self.profile(second)
            for status in ("unsure", "needs_adaptation", "none_reported"):
                response = first.put(PATH, json={"status": status}, headers=ORIGIN)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": status})
                self.assertEqual(first.get(PATH).json(), {"status": status})
                self.assertEqual(second.get(PATH).status_code, 404)
            self.assertEqual(second.put(PATH, json={"status": "needs_adaptation"},
                                        headers=ORIGIN).json(), {"status": "needs_adaptation"})
            self.assertEqual(first.get(PATH).json(), {"status": "none_reported"})
            self.assertEqual(first.get(PATH, params={"user_id": second_id}).json(),
                             {"status": "none_reported"})
            first.post("/auth/logout", headers=ORIGIN)
            self.assertEqual(first.get(PATH).status_code, 401)

    def test_invalid_and_ambiguous_inputs_preserve_previous_answer(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.sign_in(client)
            self.profile(client)
            self.assertEqual(client.put(PATH, json={"status": "unsure"}, headers=ORIGIN).status_code, 200)
            for body in ({}, {"status": None}, {"status": 1}, {"status": "cleared"},
                         {"status": "none_reported", "user_id": str(uuid4())}):
                with self.subTest(body=body):
                    self.assertEqual(client.put(PATH, json=body, headers=ORIGIN).status_code, 422)
                    self.assertEqual(client.get(PATH).json(), {"status": "unsure"})
            headers = ORIGIN | {"content-type": "application/json"}
            self.assertEqual(client.put(PATH, content=b'{"status":"unsure","status":"none_reported"}',
                                        headers=headers).status_code, 422)
            self.assertEqual(client.put(PATH, content=b" " * 2049,
                                        headers=headers).status_code, 413)
            self.assertEqual(client.get(PATH).json(), {"status": "unsure"})
