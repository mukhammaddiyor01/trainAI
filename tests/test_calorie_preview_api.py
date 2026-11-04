"""Private explicit preview contracts, owner isolation, scope checks, and no data mutation."""

import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.main import create_app
import test_accounts_database as database_tests

PATH = "/api/calorie-preview"
PROFILE = dict(age=30, height_cm=175, weight_kg=70, timezone="UTC")
ENERGY = dict(equation_sex="male", activity_category="inactive", context="general_adult")


class CaloriePreviewGuardTests(unittest.TestCase):
    def test_exact_origin_and_server_identity_are_required(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            self.assertEqual(client.post(PATH, json={"adjustment_kcal":100}).status_code, 403)
            self.assertEqual(client.post(PATH, json={"adjustment_kcal":100}, headers={"origin":"https://example.invalid"}).status_code, 403)
            self.assertEqual(client.post(PATH, json={"adjustment_kcal":100}, headers={"origin":"http://127.0.0.1","X-User-Id":"forged"}).status_code, 401)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CaloriePreviewApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def setUp(self):
        app = create_app()
        self.first = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.second = self.enterContext(TestClient(app, base_url="http://127.0.0.1"))
        self.headers = {"origin":"http://127.0.0.1"}
        for client in (self.first, self.second):
            credentials = dict(username="preview_"+uuid4().hex[:18],password="synthetic preview password")
            self.assertEqual(client.post("/auth/register",json=credentials,headers=self.headers).status_code,201)
            self.assertEqual(client.post("/auth/login",json=credentials,headers=self.headers).status_code,200)

    def save(self, client):
        self.assertEqual(client.put("/api/profile",json=PROFILE,headers=self.headers).status_code,200)
        self.assertEqual(client.put("/api/energy-preferences",json=ENERGY,headers=self.headers).status_code,200)
        self.assertEqual(client.put("/api/goal",json=dict(direction="gain",target_weight_kg=75),headers=self.headers).status_code,200)

    def preview(self, amount=100, client=None, **kwargs):
        return (client or self.first).post(PATH,json={"adjustment_kcal":amount},headers=self.headers,**kwargs)

    def test_complete_inputs_and_seven_field_preview_do_not_modify_saved_inputs(self):
        self.assertEqual(self.preview().status_code,404)
        self.first.put("/api/profile",json=PROFILE,headers=self.headers)
        self.assertEqual(self.preview().status_code,404)
        self.first.put("/api/energy-preferences",json=ENERGY,headers=self.headers)
        self.assertEqual(self.preview().status_code,404)
        self.save(self.first)
        before={path:self.first.get(path).json() for path in ("/api/profile","/api/goal","/api/energy-preferences")}
        response=self.preview()
        self.assertEqual(response.status_code,200)
        self.assertEqual(set(response.json()),{"maintenance_kcal_per_day","adjustment_kcal_per_day","preview_kcal_per_day",
                                             "goal_direction","energy_method_version","policy_version","status"})
        self.assertEqual(response.json()["status"],"preview")
        self.assertAlmostEqual(response.json()["preview_kcal_per_day"],2652.67)
        self.assertEqual(response.headers["cache-control"],"no-store")
        for path,body in before.items():
            self.assertEqual(self.first.get(path).json(),body)
        self.first.put("/api/goal",json=dict(direction="lose",target_weight_kg=65),headers=self.headers)
        self.assertAlmostEqual(self.preview().json()["preview_kcal_per_day"],2452.67)
        self.first.put("/api/goal",json=dict(direction="maintain"),headers=self.headers)
        self.assertEqual(self.preview(100).status_code,422)
        self.assertAlmostEqual(self.preview(0).json()["preview_kcal_per_day"],2552.67)

    def test_owner_and_input_spoofing_cannot_supply_other_users_or_calculated_fields(self):
        self.save(self.first)
        owner=self.first.get("/auth/me").json()["user_id"]
        self.assertEqual(self.preview(client=self.second,params={"user_id":owner}).status_code,404)
        self.save(self.second)
        self.second.put("/api/goal",json=dict(direction="lose",target_weight_kg=65),headers=self.headers)
        self.assertEqual(self.preview(client=self.second,params={"user_id":owner,"direction":"gain"}).json()["goal_direction"],"lose")
        for key,value in [("user_id",owner),("role","admin"),("profile",PROFILE),("direction","lose"),
                          ("maintenance_kcal_per_day",2000),("policy_version","forged"),("status","active")]:
            response=self.first.post(PATH,json={"adjustment_kcal":100,key:value},headers=self.headers)
            self.assertEqual(response.status_code,422)
        self.assertEqual(self.preview().json()["goal_direction"],"gain")
        self.first.post("/auth/logout",headers=self.headers)
        self.assertEqual(self.preview().status_code,401)

    def test_scope_and_current_profile_changes_cannot_return_a_stale_preview(self):
        self.save(self.first)
        self.first.put("/api/profile",json=PROFILE | dict(weight_kg=72),headers=self.headers)
        self.assertAlmostEqual(self.preview().json()["maintenance_kcal_per_day"],2580.87)
        self.assertEqual(self.first.get("/api/goal").json()["starting_weight_kg"],70)
        self.first.put("/api/profile",json=PROFILE | dict(weight_kg=75),headers=self.headers)
        self.assertEqual(self.preview().status_code,409)
        self.first.put("/api/profile",json=PROFILE,headers=self.headers)
        for change in [dict(equation_sex="unsure"),dict(activity_category="unsure"),dict(context="clinical")]:
            self.first.put("/api/energy-preferences",json=ENERGY | change,headers=self.headers)
            self.assertEqual(self.preview().status_code,409)
        self.first.put("/api/energy-preferences",json=ENERGY | dict(equation_sex="female"),headers=self.headers)
        self.assertEqual(self.preview(220).status_code,422)

    def test_invalid_missing_oversized_and_ambiguous_requests_fail_without_echo(self):
        self.save(self.first)
        for value in [None,True,"private-adjustment-marker",100.0,-1,251,[],{}]:
            response=self.preview(value)
            self.assertEqual(response.status_code,422)
            self.assertNotIn("private-adjustment-marker",response.text)
        self.assertEqual(self.first.post(PATH,json={},headers=self.headers).status_code,422)
        headers=self.headers | {"content-type":"application/json"}
        self.assertEqual(self.first.post(PATH,content=b" "*2049,headers=headers).status_code,413)
        for raw in ['{"adjustment_kcal":100,"adjustment_kcal":200}','{"adjustment_kcal":NaN}']:
            self.assertEqual(self.first.post(PATH,content=raw,headers=headers).status_code,422)
        self.assertEqual(self.preview().status_code,200)
