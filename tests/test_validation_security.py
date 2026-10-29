"""Reject ambiguous input and verify explicit public response fields."""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.main import create_app
from backend.schemas import AccountResponse, Credentials


class ValidationSecurityTests(unittest.TestCase):
    def test_credential_schema_does_not_coerce_or_accept_extra_fields(self):
        base = {"username": "member", "password": "synthetic test passphrase"}
        for payload in [{**base, "password": True}, {**base, "username": 123},
                        {**base, "user_id": str(uuid4())}, {**base, "role": "admin"},
                        {**base, "password": "invalid\x00passphrase"},
                        {**base, "password": "synthetic\ud800passphrase"}]:
            with self.subTest(fields=list(payload)), self.assertRaises(ValidationError):
                Credentials.model_validate(payload)
        self.assertNotIn(base["password"], repr(Credentials.model_validate(base)))

    def test_duplicate_fields_nonfinite_values_and_arrays_are_rejected(self):
        bodies = ['{"username":"first","username":"second","password":"synthetic passphrase"}',
                  '{"username":"member","password":NaN}', '[]', 'null',
                  '{"username":"member","password":true}']
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            for body in bodies:
                with self.subTest(body=body):
                    response = client.post("/auth/register", content=body, headers={
                        "origin": "http://127.0.0.1", "content-type": "application/json",
                    })
                    self.assertEqual(response.status_code, 422)
                    self.assertNotIn("synthetic passphrase", response.text)

    def test_account_response_excludes_secrets_and_internal_fields(self):
        value = AccountResponse.model_validate({"user_id": uuid4(), "username": "member",
                                               "password_hash": "private-hash", "token": "private-token",
                                               "role": "admin"})
        self.assertEqual(set(value.model_dump()), {"user_id", "username"})
