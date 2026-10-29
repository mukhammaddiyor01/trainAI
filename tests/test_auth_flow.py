"""Full synthetic authentication flow through HTTP and isolated PostgreSQL."""

import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app
from backend.session_tokens import SESSION_COOKIE
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class AuthFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def test_two_accounts_sign_in_in_isolation_and_logout(self):
        headers = {"origin": "http://127.0.0.1"}
        with TestClient(create_app(), base_url="http://127.0.0.1") as first:
            with TestClient(create_app(), base_url="http://127.0.0.1") as second:
                identities = []
                for client in [first, second]:
                    credentials = {"username": "flow_" + uuid4().hex[:20], "password": "synthetic test passphrase"}
                    registered = client.post("/auth/register", headers=headers, json=credentials)
                    self.assertEqual(registered.status_code, 201)
                    self.assertEqual(client.get("/auth/me").status_code, 401)
                    logged_in = client.post("/auth/login", headers=headers, json=credentials)
                    self.assertEqual(logged_in.status_code, 200)
                    self.assertIn("HttpOnly", logged_in.headers["set-cookie"])
                    self.assertIn("SameSite=strict", logged_in.headers["set-cookie"])
                    self.assertNotIn("token", logged_in.json())
                    identities.append(logged_in.json())
                self.assertNotEqual(identities[0]["user_id"], identities[1]["user_id"])
                self.assertEqual(first.get("/auth/me", params={"user_id": identities[1]["user_id"]}).json(), identities[0])
                self.assertEqual(second.get("/auth/me").json(), identities[1])
                self.assertIn(identities[0]["username"], first.get("/account").text)
                self.assertNotIn(identities[1]["username"], first.get("/account").text)
                self.assertEqual(first.post("/auth/logout", headers=headers).status_code, 204)
                self.assertIsNone(first.cookies.get(SESSION_COOKIE))
                self.assertEqual(first.get("/auth/me").status_code, 401)
                self.assertEqual(second.get("/auth/me").status_code, 200)
