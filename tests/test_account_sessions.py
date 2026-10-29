"""Synthetic account/session flows in the isolated PostgreSQL runner."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.accounts import (InvalidCredentials, UsernameUnavailable, account_for_token,
                              authenticate_account, create_login_session, register_account,
                              revoke_login_session)
from backend.database import close_database, session_scope
from backend.models import LoginSession, User
from backend.session_tokens import token_digest
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class AccountSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def new_account(self):
        return register_account("member_" + uuid4().hex[:20], "synthetic passphrase for tests")

    def test_registration_and_authentication_never_store_plaintext(self):
        identity = self.new_account()
        self.assertEqual(authenticate_account(identity.username.upper(), "synthetic passphrase for tests"), identity)
        with session_scope() as session:
            stored = session.get(User, identity.user_id)
            self.assertTrue(stored.password_hash.startswith("$argon2id$"))
            self.assertNotEqual(stored.password_hash, "synthetic passphrase for tests")
        with self.assertRaises(UsernameUnavailable):
            register_account(identity.username.upper(), "another synthetic passphrase")
        for username, password in [(identity.username, "wrong synthetic passphrase"),
                                   ("unknown_" + uuid4().hex[:20], "synthetic passphrase for tests")]:
            with self.assertRaisesRegex(InvalidCredentials, "Username or password is incorrect"):
                authenticate_account(username, password)

    def test_identity_is_derived_from_token_and_logout_revokes_access(self):
        first, second = self.new_account(), self.new_account()
        token = create_login_session(first)
        other = create_login_session(second)
        self.assertEqual(account_for_token(token), first)
        self.assertEqual(account_for_token(other), second)
        with session_scope() as session:
            self.assertIsNotNone(session.get(LoginSession, token_digest(token)))
            self.assertIsNone(session.get(LoginSession, token))
        revoke_login_session(token)
        revoke_login_session(token)
        self.assertIsNone(account_for_token(token))
        self.assertEqual(account_for_token(other), second)

    def test_login_rotates_previous_token_and_expiry_is_enforced(self):
        identity = self.new_account()
        first = create_login_session(identity)
        second = create_login_session(identity, previous_token=first)
        self.assertNotEqual(first, second)
        self.assertIsNone(account_for_token(first))
        now = datetime.now(timezone.utc)
        with session_scope() as session:
            record = session.get(LoginSession, token_digest(second))
            record.created_at = now - timedelta(days=2)
            record.expires_at = now - timedelta(days=1)
        self.assertIsNone(account_for_token(second))
        self.assertIsNone(account_for_token("invalid-token"))


if __name__ == "__main__":
    unittest.main()
