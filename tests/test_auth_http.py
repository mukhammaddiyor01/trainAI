"""Authentication request boundaries without a database."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.config import DatabaseConfigurationError
from backend.main import create_app


class AuthHttpBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.client = self.enterContext(TestClient(create_app(), base_url="http://127.0.0.1"))
        self.origin = {"origin": "http://127.0.0.1"}

    def test_writes_require_exact_same_origin(self):
        for path in ["/auth/login", "/auth/register", "/auth/logout"]:
            for origin in [None, "http://untrusted.example", "http://localhost"]:
                headers = {"origin": origin} if origin else {}
                with self.subTest(path=path, origin=origin):
                    self.assertEqual(self.client.post(path, headers=headers, json={}).status_code, 403)

    def test_credentials_are_bounded_and_never_reflected(self):
        private_text = "synthetic-private-password"
        cases = [({}, 422), ({"username": [], "password": private_text}, 422),
                 ({"username": "member", "password": private_text, "user_id": 1}, 422),
                 ({"username": "member", "password": "x" * 129}, 422),
                 ({"username": "member", "password": "x" * 3000}, 413)]
        for payload, status in cases:
            with self.subTest(status=status):
                response = self.client.post("/auth/login", headers=self.origin, json=payload)
                self.assertEqual(response.status_code, status)
                self.assertNotIn(private_text, response.text)
        self.assertEqual(self.client.post("/auth/login", headers=self.origin, content="bad-json").status_code, 415)
        response = self.client.post("/auth/login", headers={**self.origin, "content-type": "application/json"}, content="{")
        self.assertEqual(response.status_code, 422)

    def test_anonymous_identity_and_unconfigured_database_fail_clearly(self):
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        with patch("backend.auth_routes.register_account", side_effect=DatabaseConfigurationError("private-value")):
            response = self.client.post("/auth/register", headers=self.origin,
                                        json={"username": "member", "password": "synthetic test passphrase"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private-value", response.text)
