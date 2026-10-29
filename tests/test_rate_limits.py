"""Rolling-window expiry, bounded state, and actual HTTP throttling."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.accounts import InvalidCredentials
from backend.main import create_app
from backend.rate_limits import AttemptLimiter


class RateLimitTests(unittest.TestCase):
    def test_window_expires_and_bucket_capacity_fails_closed(self):
        now = [0.0]
        limiter = AttemptLimiter(clock=lambda: now[0], max_buckets=1)
        self.assertEqual(limiter.check("login", "first", 2), 0)
        self.assertEqual(limiter.check("login", "first", 2), 0)
        self.assertEqual(limiter.check("login", "first", 2), 60)
        self.assertGreater(limiter.check("login", "second", 2), 0)
        now[0] = 60.0
        self.assertEqual(limiter.check("login", "second", 2), 0)
        self.assertEqual(len(limiter.buckets), 1)
        self.assertNotIn("second", repr(limiter.buckets))

    def test_account_attempt_limit_uses_normalized_username(self):
        with patch("backend.auth_routes.sign_in", side_effect=InvalidCredentials("Username or password is incorrect.")) as sign_in:
            with TestClient(create_app(), base_url="http://127.0.0.1") as client:
                for attempt in range(8):
                    username = "Member" if attempt % 2 else "  MEMBER  "
                    response = client.post("/auth/login", headers={"origin": "http://127.0.0.1"},
                                           json={"username": username, "password": "synthetic test passphrase"})
                    self.assertEqual(response.status_code, 401)
                response = client.post("/auth/login", headers={"origin": "http://127.0.0.1"},
                                       json={"username": "member", "password": "synthetic test passphrase"})
                self.assertEqual(response.status_code, 429)
                self.assertGreaterEqual(int(response.headers["retry-after"]), 1)
                self.assertEqual(sign_in.call_count, 8)

    def test_peer_limit_also_bounds_invalid_payload_attempts(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            for attempt in range(30):
                self.assertEqual(client.post("/auth/register", headers={"origin": "http://127.0.0.1"}, json={}).status_code, 422)
            self.assertEqual(client.post("/auth/register", headers={"origin": "http://127.0.0.1"}, json={}).status_code, 429)
