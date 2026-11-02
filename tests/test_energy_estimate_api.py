"""Estimates use current owner inputs, expose only approved fields, and retain scope guards."""

import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.main import create_app
import test_accounts_database as database_tests

PATH = "/api/energy-estimate"
PREFERENCES = dict(equation_sex="male", activity_category="active", context="general_adult")
PROFILE = dict(age=30, height_cm=175, weight_kg=70, timezone="UTC")


class EnergyEstimateGuardTests(unittest.TestCase):
    def test_anonymous_and_forged_identity_are_rejected(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.get(PATH, headers={"X-User-Id":"forged", "Authorization":"Bearer forged"}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class EnergyEstimateApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def setUp(self):
        app = create_app()
        self.first = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.second = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.headers = {"origin":"http://127.0.0.1"}
        for client in (self.first, self.second):
            credentials = dict(username="estimate_" + uuid4().hex[:16], password="synthetic energy password")
            self.assertEqual(client.post("/auth/register", json=credentials, headers=self.headers).status_code, 201)
            self.assertEqual(client.post("/auth/login", json=credentials, headers=self.headers).status_code, 200)

    def save(self, client, preferences=PREFERENCES, profile=PROFILE):
        self.assertEqual(client.put("/api/profile", json=profile, headers=self.headers).status_code, 200)
        self.assertEqual(client.put("/api/energy-preferences", json=preferences, headers=self.headers).status_code, 200)

    def test_missing_inputs_no_backfill_and_current_weight_instead_of_goal_snapshot(self):
        self.assertEqual(self.first.get(PATH).status_code, 404)
        self.first.put("/api/profile", json=PROFILE, headers=self.headers)
        self.assertEqual(self.first.get(PATH).status_code, 404)
        self.save(self.first)
        before = self.first.get(PATH)
        self.assertAlmostEqual(before.json()["energy_kcal_per_day"], 2934.62)
        self.assertEqual(set(before.json()), {"energy_kcal_per_day","method_version","equation_sex","activity_category"})
        self.assertEqual(before.json()["method_version"], "dri-2023-adult-eer-v1")
        self.assertEqual(before.headers["cache-control"], "no-store")
        self.assertEqual(self.first.put("/api/goal", json=dict(direction="gain", target_weight_kg=90), headers=self.headers).status_code, 200)
        self.first.put("/api/profile", json=PROFILE | dict(weight_kg=80), headers=self.headers)
        self.assertAlmostEqual(self.first.get(PATH).json()["energy_kcal_per_day"], 3093.72)
        self.assertEqual(self.first.get("/api/goal").json()["starting_weight_kg"], 70)

    def test_cross_owner_and_query_input_spoofing_do_not_change_estimate(self):
        self.save(self.first)
        other = self.first.get("/auth/me").json()["user_id"]
        self.assertEqual(self.second.get(PATH, params={"user_id":other}, headers={"X-User-Id":other}).status_code, 404)
        self.save(self.second, PREFERENCES | dict(equation_sex="female", activity_category="inactive"))
        response = self.second.get(PATH, params={"user_id":other,"weight_kg":500,"equation_sex":"male"}, headers={"X-User-Id":other})
        self.assertAlmostEqual(response.json()["energy_kcal_per_day"], 2195.30)
        self.assertAlmostEqual(self.first.get(PATH).json()["energy_kcal_per_day"], 2934.62)
        self.first.post("/auth/logout", headers=self.headers)
        self.assertEqual(self.first.get(PATH).status_code, 401)

    def test_uncertain_excluded_age_and_nonpositive_results_do_not_return_stale_estimates(self):
        self.save(self.first)
        self.assertEqual(self.first.get(PATH).status_code, 200)
        for change in [dict(equation_sex="unsure"), dict(activity_category="unsure"), dict(context="unsure"),
                       dict(context="pregnant"), dict(context="breastfeeding"), dict(context="clinical")]:
            body = PREFERENCES | change
            self.first.put("/api/energy-preferences", json=body, headers=self.headers)
            self.assertEqual(self.first.get(PATH).status_code, 409)
            self.assertEqual(self.first.get("/api/energy-preferences").json(), body)
        self.save(self.first, profile=PROFILE | dict(age=18))
        self.assertEqual(self.first.get(PATH).status_code, 409)
        self.save(self.first, PREFERENCES | dict(activity_category="very_active"),
                  PROFILE | dict(age=120,height_cm=50,weight_kg=20))
        self.assertEqual(self.first.get(PATH).status_code, 409)
