"""Separate local instances must not consume one another's session cookies."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import create_app
from backend.session_tokens import session_cookie_name


class CookieNameTests(unittest.TestCase):
    def test_cookie_name_is_explicit_and_invalid_config_fails_closed(self):
        with patch.dict(os.environ, {"TRAINAI_COOKIE_NAME": "trainai_test_instance"}):
            self.assertEqual(session_cookie_name(), "trainai_test_instance")
        for invalid in ["", "has space", "bad;cookie", "x" * 49]:
            with patch.dict(os.environ, {"TRAINAI_COOKIE_NAME": invalid}):
                with self.assertRaises(ValueError):
                    session_cookie_name()

    def test_guard_ignores_another_instances_cookie(self):
        with patch("backend.guards.account_for_token", return_value=None) as lookup:
            with TestClient(create_app(), base_url="http://127.0.0.1") as client:
                client.cookies.set("another_instance_session", "A" * 43)
                self.assertEqual(client.get("/auth/me").status_code, 401)
            lookup.assert_called_once_with(None)
