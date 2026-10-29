"""Protected routes use one server-side identity guard."""

import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.accounts import AccountIdentity
from backend.main import create_app
from backend.session_tokens import SESSION_COOKIE


class GuardTests(unittest.TestCase):
    def test_missing_invalid_and_expired_sessions_cannot_access_identity(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            with patch("backend.guards.account_for_token", return_value=None):
                for token in [None, "invalid", "A" * 43]:
                    client.cookies.clear()
                    if token:
                        client.cookies.set(SESSION_COOKIE, token)
                    self.assertEqual(client.get("/auth/me").status_code, 401)
                    response = client.get("/account", follow_redirects=False)
                    self.assertEqual(response.status_code, 303)

    def test_query_or_header_user_id_cannot_replace_guard_identity(self):
        identity = AccountIdentity(uuid4(), "guard_member")
        with patch("backend.guards.account_for_token", return_value=identity):
            with TestClient(create_app(), base_url="http://127.0.0.1") as client:
                response = client.get("/auth/me", params={"user_id": str(uuid4())},
                                      headers={"X-User-Id": str(uuid4()), "Authorization": "Bearer forged"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["user_id"], str(identity.user_id))
