"""Profile persistence is isolated by the server-selected owner's primary key."""

import os
import unittest
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.models import Profile
from backend.profiles import read_profile, save_profile
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class ProfileStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def test_profiles_are_isolated_and_updates_do_not_create_duplicates(self):
        first = register_account("profile_" + uuid4().hex[:20], "synthetic test passphrase")
        second = register_account("profile_" + uuid4().hex[:20], "synthetic test passphrase")
        details = validate_profile(30, 175, 72, "Asia/Seoul")
        self.assertIsNone(read_profile(first.user_id))
        save_profile(first.user_id, details)
        self.assertEqual(read_profile(first.user_id), details)
        self.assertIsNone(read_profile(second.user_id))
        updated = validate_profile(31, 175, 73, "UTC")
        save_profile(first.user_id, updated)
        self.assertEqual(read_profile(first.user_id), updated)
        self.assertIsNone(read_profile(second.user_id))

    def test_database_bounds_and_ownership_foreign_key_are_enforced(self):
        account = register_account("bounds_" + uuid4().hex[:20], "synthetic test passphrase")
        with self.assertRaises(IntegrityError):
            with session_scope() as session:
                session.add(Profile(user_id=account.user_id, age=17, height_cm=170,
                                    weight_kg=70, timezone="UTC"))
        with self.assertRaises(IntegrityError):
            with session_scope() as session:
                session.add(Profile(user_id=uuid4(), age=25, height_cm=170,
                                    weight_kg=70, timezone="UTC"))
