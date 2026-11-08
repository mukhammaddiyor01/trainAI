"""Private readiness page reports saved inputs without prescribing a workout."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
import test_accounts_database as database_tests


class WorkoutReadinessGuardTests(unittest.TestCase):
    def test_anonymous_redirect_and_local_styles(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.get("/workout-readiness", follow_redirects=False)
            self.assertEqual((response.status_code, response.headers["location"]), (303, "/login"))
            self.assertEqual(client.get("/static/css/workout-readiness.css").status_code, 200)


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WorkoutReadinessPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def sign_in(self, client):
        credentials = dict(username="workout_page_" + uuid4().hex[:12], password="synthetic workout password")
        headers = {"origin": "http://127.0.0.1"}
        self.assertEqual(client.post("/auth/register", json=credentials, headers=headers).status_code, 201)
        self.assertEqual(client.post("/auth/login", json=credentials, headers=headers).status_code, 200)
        return headers

    def profile(self, client, headers):
        self.assertEqual(client.put("/api/profile", json={
            "age": 30, "height_cm": 175, "weight_kg": 70, "timezone": "UTC",
        }, headers=headers).status_code, 200)

    def test_profile_first_empty_and_saved_states(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            headers = self.sign_in(client)
            self.assertEqual(client.get("/workout-readiness", follow_redirects=False).headers["location"], "/profile")
            self.profile(client, headers)
            empty = client.get("/workout-readiness")
            self.assertIn("Add training choices", empty.text)
            self.assertIn("Add your answer", empty.text)
            self.assertNotIn("Equipment available", empty.text)
            self.assertIn('href="/workout-readiness"', client.get("/account").text)
            self.assertEqual(client.put("/api/training-preferences", json={
                "experience": "beginner", "activity": "mostly_seated", "equipment": [],
                "weekdays": [1, 3], "session_minutes": 30,
            }, headers=headers).status_code, 200)
            self.assertEqual(client.put("/api/movement-limitations", json={
                "status": "none_reported",
            }, headers=headers).status_code, 200)
            saved = client.get("/workout-readiness")
            for phrase in ("1 possible two-day pair", "Equipment available",
                           "Required equipment unavailable", "No limitations reported",
                           "No workout has been created", "Prescription review pending",
                           "Monday and Wednesday", "not scheduled workouts"):
                self.assertIn(phrase, saved.text)
            self.assertEqual(saved.headers["cache-control"], "no-store")
            self.assertEqual(client.put("/api/training-preferences", json={
                "experience": "beginner", "activity": "mostly_seated", "equipment": [],
                "weekdays": [1, 2], "session_minutes": 30,
            }, headers=headers).status_code, 200)
            adjacent = client.get("/workout-readiness")
            self.assertIn("No two-day pair has a rest day", adjacent.text)
            self.assertNotIn("See possible day pairs", adjacent.text)

    def test_query_owner_spoofing_cannot_show_another_answer(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as first:
            with TestClient(create_app(), base_url="http://127.0.0.1") as second:
                first_headers, second_headers = self.sign_in(first), self.sign_in(second)
                self.profile(first, first_headers)
                self.profile(second, second_headers)
                self.assertEqual(first.put("/api/movement-limitations", json={
                    "status": "needs_adaptation",
                }, headers=first_headers).status_code, 200)
                for client, headers, days in ((first, first_headers, [1, 3]),
                                              (second, second_headers, [2, 4])):
                    self.assertEqual(client.put("/api/training-preferences", json={
                        "experience": "beginner", "activity": "mostly_seated", "equipment": [],
                        "weekdays": days, "session_minutes": 30,
                    }, headers=headers).status_code, 200)
                first_id = first.get("/auth/me").json()["user_id"]
                page = second.get("/workout-readiness", params={"user_id": first_id})
                self.assertIn("Add your answer", page.text)
                self.assertNotIn("Adapted activity needed", page.text)
                self.assertIn("Tuesday and Thursday", page.text)
                self.assertNotIn("Monday and Wednesday", page.text)
