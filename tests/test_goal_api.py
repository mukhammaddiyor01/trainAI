"""Goal API guards, strict validation, snapshots, and two-user isolation."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class GoalApiGuardTests(unittest.TestCase):
    def test_goal_access_requires_identity_and_writes_require_origin(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get("/api/goal").status_code, 401)
            self.assertEqual(client.put("/api/goal", json={}).status_code, 403)
            self.assertEqual(client.put("/api/goal", headers={"origin": "http://127.0.0.1"}, json={}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class GoalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def setUp(self):
        self.app = create_app()
        self.first = self.enterContext(TestClient(self.app, base_url="http://127.0.0.1"))
        self.second = self.enterContext(TestClient(self.app, base_url="http://127.0.0.1"))
        self.headers = {"origin": "http://127.0.0.1"}
        for client in [self.first, self.second]:
            values = {"username": "goalapi_" + uuid4().hex[:18], "password": "synthetic goal passphrase"}
            self.assertEqual(client.post("/auth/register", headers=self.headers, json=values).status_code, 201)
            self.assertEqual(client.post("/auth/login", headers=self.headers, json=values).status_code, 200)

    def save_profile(self, client, weight):
        response = client.put("/api/profile", headers=self.headers,
                              json={"age": 30, "height_cm": 175.0, "weight_kg": weight, "timezone": "UTC"})
        self.assertEqual(response.status_code, 200)

    def test_profile_is_required_and_server_weight_cannot_be_overridden(self):
        body = {"direction": "gain", "target_weight_kg": 75.0}
        self.assertEqual(self.first.put("/api/goal", headers=self.headers, json=body).status_code, 409)
        self.save_profile(self.first, 60.0)
        for key, value in [("user_id", str(uuid4())), ("starting_weight_kg", 50.0), ("role", "admin")]:
            self.assertEqual(self.first.put("/api/goal", headers=self.headers, json={**body, key: value}).status_code, 422)
        response = self.first.put("/api/goal", headers=self.headers, json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {**body, "starting_weight_kg": 60.0})

    def test_user_cannot_read_or_replace_another_users_goal(self):
        self.save_profile(self.first, 60.0)
        self.save_profile(self.second, 90.0)
        self.assertEqual(self.first.put("/api/goal", headers=self.headers,
                                       json={"direction": "gain", "target_weight_kg": 75.0}).status_code, 200)
        other_id = self.first.get("/auth/me").json()["user_id"]
        self.assertEqual(self.second.get("/api/goal", params={"user_id": other_id}).status_code, 404)
        self.assertEqual(self.second.put("/api/goal", headers=self.headers,
                                        json={"direction": "lose", "target_weight_kg": 80.0}).status_code, 200)
        self.assertEqual(self.first.get("/api/goal").json()["target_weight_kg"], 75.0)
        self.assertEqual(self.second.get("/api/goal").json()["target_weight_kg"], 80.0)

    def test_invalid_goals_preserve_previous_values_and_maintenance_uses_null(self):
        self.save_profile(self.first, 60.0)
        body = {"direction": "gain", "target_weight_kg": 75.0}
        self.assertEqual(self.first.put("/api/goal", headers=self.headers, json=body).status_code, 200)
        for values in [{"direction": "gain"}, {"direction": "gain", "target_weight_kg": 55},
                       {"direction": "lose", "target_weight_kg": "55"},
                       {"direction": "gain", "target_weight_kg": True},
                       {"direction": "maintain", "target_weight_kg": 60}, {"direction": "bulk"}]:
            self.assertEqual(self.first.put("/api/goal", headers=self.headers, json=values).status_code, 422)
        self.assertEqual(self.first.get("/api/goal").json()["target_weight_kg"], 75.0)
        response = self.first.put("/api/goal", headers=self.headers, json={"direction": "maintain"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["target_weight_kg"])
