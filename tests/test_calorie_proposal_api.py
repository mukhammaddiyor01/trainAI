"""Proposal writes require owner identity, exact origin, and current saved inputs."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class CalorieProposalPublicGuardTests(unittest.TestCase):
    def test_anonymous_and_missing_origin_fail(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.post("/api/calorie-proposals", json={"adjustment_kcal": 100}).status_code, 403)
            self.assertEqual(client.post("/api/calorie-proposals", json={"adjustment_kcal": 100},
                                         headers={"origin": "http://127.0.0.1"}).status_code, 401)
            self.assertEqual(client.get(f"/api/calorie-proposals/{uuid4()}").status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CalorieProposalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = dict(username="proposal_api_" + uuid4().hex[:12], password="synthetic proposal password")
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def inputs(self, client, headers, *, direction="gain"):
        self.assertEqual(client.put("/api/profile", json={
            "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
        }, headers=headers).status_code, 200)
        goal = {"direction": direction}
        if direction == "gain":
            goal["target_weight_kg"] = 75
        self.assertEqual(client.put("/api/goal", json=goal, headers=headers).status_code, 200)
        self.assertEqual(client.put("/api/energy-preferences", json={
            "equation_sex": "male", "activity_category": "inactive", "context": "general_adult",
        }, headers=headers).status_code, 200)

    def test_create_read_allowlist_and_two_owner_isolation(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers = self.sign_in(first)
            self.sign_in(second)
            self.inputs(first, headers)
            created = first.post("/api/calorie-proposals", json={"adjustment_kcal": 200}, headers=headers)
            self.assertEqual(created.status_code, 201)
            self.assertEqual(set(created.json()), {"proposal_id", "created_at", "status",
                                                  "maintenance_kcal_per_day", "adjustment_kcal_per_day",
                                                  "preview_kcal_per_day", "goal_direction",
                                                  "energy_method_version", "policy_version"})
            self.assertEqual(created.json()["status"], "pending")
            self.assertAlmostEqual(created.json()["preview_kcal_per_day"], 2752.67)
            proposal_id = created.json()["proposal_id"]
            self.assertEqual(first.get(f"/api/calorie-proposals/{proposal_id}").json(), created.json())
            self.assertEqual(second.get(f"/api/calorie-proposals/{proposal_id}").status_code, 404)
            self.assertEqual(second.get(f"/api/calorie-proposals/{proposal_id}?user_id=other").status_code, 404)
            self.assertEqual(first.get("/api/goal").json()["direction"], "gain")
            self.assertEqual(first.get("/api/energy-preferences").json()["equation_sex"], "male")
            first.post("/auth/logout", headers=headers)
            self.assertEqual(first.get(f"/api/calorie-proposals/{proposal_id}").status_code, 401)

    def test_prerequisites_scope_and_forged_fields(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = self.sign_in(client)
            self.assertEqual(client.post("/api/calorie-proposals", json={"adjustment_kcal": 100}, headers=headers).status_code, 404)
            self.inputs(client, headers)
            for extra in ("user_id", "goal_direction", "preview_kcal_per_day", "status", "policy_version"):
                with self.subTest(extra=extra):
                    body = {"adjustment_kcal": 100, extra: "forged"}
                    self.assertEqual(client.post("/api/calorie-proposals", json=body, headers=headers).status_code, 422)
            for invalid in (None, True, "100", 100.0, -1, 251):
                with self.subTest(invalid=invalid):
                    self.assertEqual(client.post("/api/calorie-proposals", json={"adjustment_kcal": invalid},
                                                 headers=headers).status_code, 422)
            duplicate = client.post("/api/calorie-proposals", content=b'{"adjustment_kcal":100,"adjustment_kcal":200}',
                                    headers=headers | {"content-type": "application/json"})
            self.assertEqual(duplicate.status_code, 422)
            oversized = client.post("/api/calorie-proposals", content=b" " * 2049,
                                    headers=headers | {"content-type": "application/json"})
            self.assertEqual(oversized.status_code, 413)
            self.assertNotIn("forged", oversized.text)
            self.assertEqual(client.post("/api/calorie-proposals", json={"adjustment_kcal": 0}, headers=headers).status_code, 422)
            self.assertEqual(client.post("/api/calorie-proposals", json={"adjustment_kcal": 251}, headers={
                "origin": "http://example.com"}).status_code, 403)
            self.assertEqual(client.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 75, "timezone": "UTC",
            }, headers=headers).status_code, 200)
            self.assertEqual(client.post("/api/calorie-proposals", json={"adjustment_kcal": 100}, headers=headers).status_code, 409)
