"""Profile API mass-assignment, strict validation, and two-user isolation."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class ProfileApiGuardTests(unittest.TestCase):
    def test_profile_access_requires_authentication_and_writes_require_origin(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get("/api/profile").status_code, 401)
            self.assertEqual(client.put("/api/profile", json={}).status_code, 403)
            self.assertEqual(client.put("/api/profile", headers={"origin": "http://127.0.0.1"}, json={}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class ProfileApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        credentials = {"username": "api_" + uuid4().hex[:20], "password": "synthetic test passphrase"}
        headers = {"origin": "http://127.0.0.1"}
        self.assertEqual(client.post("/auth/register", headers=headers, json=credentials).status_code, 201)
        response = client.post("/auth/login", headers=headers, json=credentials)
        self.assertEqual(response.status_code, 200)
        return response.json()["user_id"]

    def test_two_users_cannot_read_or_replace_each_others_profile(self):
        headers = {"origin": "http://127.0.0.1"}
        profile = {"age": 30, "height_cm": 175.0, "weight_kg": 72.0, "timezone": "Asia/Seoul"}
        app = create_app()
        with TestClient(app, base_url="http://127.0.0.1") as first:
            with TestClient(app, base_url="http://127.0.0.1") as second:
                first_id, second_id = self.sign_in(first), self.sign_in(second)
                self.assertEqual(first.get("/api/profile").status_code, 404)
                self.assertEqual(first.put("/api/profile", headers=headers, json=profile).status_code, 200)
                self.assertEqual(second.get("/api/profile", params={"user_id": first_id}).status_code, 404)
                for field, value in [("user_id", second_id), ("role", "admin")]:
                    response = first.put("/api/profile", headers=headers, json={**profile, field: value})
                    self.assertEqual(response.status_code, 422)
                self.assertEqual(second.get("/api/profile").status_code, 404)
                self.assertEqual(first.get("/api/profile", params={"user_id": second_id}).json(), profile)
                self.assertEqual(second.put("/api/profile", headers=headers, json={**profile, "age": 35}).status_code, 200)
                self.assertEqual(first.get("/api/profile").json()["age"], 30)
                invalid = [{"age": True}, {"age": "30"}, {"age": 17}, {"weight_kg": "72"},
                           {"weight_kg": None}, {"timezone": "not-a-zone"}]
                for change in invalid:
                    self.assertEqual(first.put("/api/profile", headers=headers, json={**profile, **change}).status_code, 422)
                self.assertEqual(first.get("/api/profile").json(), profile)
