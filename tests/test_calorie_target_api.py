"""Approval API requires explicit consent and owner-only current state."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class CalorieTargetPublicGuardTests(unittest.TestCase):
    def test_anonymous_and_missing_origin_rejected(self):
        proposal = uuid4()
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            path = f"/api/calorie-proposals/{proposal}/approve"
            self.assertEqual(client.post(path, json={"confirm": True}).status_code, 403)
            self.assertEqual(client.post(path, json={"confirm": True},
                                         headers={"origin": "http://127.0.0.1"}).status_code, 401)
            self.assertEqual(client.get("/api/calorie-targets/active").status_code, 401)
            self.assertEqual(client.get("/api/calorie-targets").status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CalorieTargetApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        headers = {"origin": "http://127.0.0.1"}
        credentials = dict(username="target_api_" + uuid4().hex[:12], password="synthetic target password")
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def inputs(self, client, headers):
        self.assertEqual(client.put("/api/profile", json={
            "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
        }, headers=headers).status_code, 200)
        self.assertEqual(client.put("/api/goal", json={
            "direction": "gain", "target_weight_kg": 75,
        }, headers=headers).status_code, 200)
        self.assertEqual(client.put("/api/energy-preferences", json={
            "equation_sex": "male", "activity_category": "inactive", "context": "general_adult",
        }, headers=headers).status_code, 200)

    def test_approval_is_explicit_allowlisted_private_and_idempotent(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first, TestClient(create_app(), base_url="http://127.0.0.1") as second:
            headers = self.sign_in(first)
            self.sign_in(second)
            self.assertEqual(first.get("/api/calorie-targets/active").status_code, 404)
            self.inputs(first, headers)
            created = first.post("/api/calorie-proposals", json={"adjustment_kcal": 100}, headers=headers).json()
            path = f"/api/calorie-proposals/{created['proposal_id']}/approve"
            self.assertEqual(second.post(path, json={"confirm": True}, headers=headers).status_code, 404)
            for invalid in ({}, {"confirm": False}, {"confirm": 1}, {"confirm": True, "status": "active"}):
                with self.subTest(invalid=invalid):
                    self.assertEqual(first.post(path, json=invalid, headers=headers).status_code, 422)
            self.assertEqual(first.post(path, json={"confirm": True},
                                        headers={"origin": "http://example.com"}).status_code, 403)
            response = first.post(path, json={"confirm": True}, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.json()), {"target_id", "proposal_id", "version", "status",
                                                    "target_kcal_per_day", "approved_at"})
            self.assertEqual((response.json()["version"], response.json()["status"]), (1, "active"))
            self.assertEqual(first.post(path, json={"confirm": True}, headers=headers).json(), response.json())
            self.assertEqual(first.get("/api/calorie-targets/active").json(), response.json())
            self.assertEqual(first.get("/api/calorie-targets").json(), {"items": [response.json()]})
            self.assertEqual(second.get("/api/calorie-targets/active").status_code, 404)
            self.assertEqual(second.get("/api/calorie-targets").json(), {"items": []})
            self.assertEqual(first.get(f"/api/calorie-proposals/{created['proposal_id']}").json()["status"], "approved")
            first.post("/auth/logout", headers=headers)
            self.assertEqual(first.get("/api/calorie-targets/active").status_code, 401)

    def test_stale_inputs_and_invalid_json_never_approve(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = self.sign_in(client)
            self.inputs(client, headers)
            created = client.post("/api/calorie-proposals", json={"adjustment_kcal": 100}, headers=headers).json()
            path = f"/api/calorie-proposals/{created['proposal_id']}/approve"
            self.assertEqual(client.post(path, content=b'{"confirm":true,"confirm":true}',
                                         headers=headers | {"content-type": "application/json"}).status_code, 422)
            self.assertEqual(client.post(path, content=b" " * 2049,
                                         headers=headers | {"content-type": "application/json"}).status_code, 413)
            self.assertEqual(client.put("/api/profile", json={
                "age": 30, "height_cm": 175, "weight_kg": 71, "timezone": "UTC",
            }, headers=headers).status_code, 200)
            response = client.post(path, json={"confirm": True}, headers=headers)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(client.get("/api/calorie-targets/active").status_code, 404)
            self.assertEqual(client.get(f"/api/calorie-proposals/{created['proposal_id']}").json()["status"], "pending")

    def test_history_preserves_superseded_versions(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = self.sign_in(client)
            self.inputs(client, headers)
            first_proposal = client.post("/api/calorie-proposals", json={"adjustment_kcal": 100},
                                         headers=headers).json()
            first_path = f"/api/calorie-proposals/{first_proposal['proposal_id']}/approve"
            first = client.post(first_path, json={"confirm": True}, headers=headers).json()
            second_proposal = client.post("/api/calorie-proposals", json={"adjustment_kcal": 200},
                                          headers=headers).json()
            second = client.post(f"/api/calorie-proposals/{second_proposal['proposal_id']}/approve",
                                 json={"confirm": True}, headers=headers).json()
            history = client.get("/api/calorie-targets").json()["items"]
            self.assertEqual([(item["version"], item["status"]) for item in history],
                             [(2, "active"), (1, "superseded")])
            self.assertEqual(history[0]["target_id"], second["target_id"])
            self.assertEqual(history[1]["target_id"], first["target_id"])
            self.assertEqual(client.get("/api/calorie-targets/active").json(), second)
            self.assertEqual(client.post(first_path, json={"confirm": True},
                                         headers=headers).json(), history[1])
