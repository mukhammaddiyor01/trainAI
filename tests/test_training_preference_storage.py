"""Actual PostgreSQL ownership, atomic saves, constraints, and migration parity."""

from concurrent.futures import ThreadPoolExecutor
import os
import unittest
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.models import TrainingPreferences
from backend.profiles import save_profile
from backend.services.profiles import validate_profile
from backend.services.training_preferences import validate_training_preferences
from backend.training_preferences import read_training_preferences, save_training_preferences
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class TrainingPreferenceStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("training_" + uuid4().hex[:20], "synthetic test passphrase")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        return identity.user_id

    def test_round_trip_is_owner_scoped_and_updates_replace_all_fields(self):
        first, second = self.owner(), self.owner()
        self.assertIsNone(read_training_preferences(first))
        original = validate_training_preferences("beginner", "mostly_seated", [], [1], 10)
        save_training_preferences(first, original)
        self.assertEqual(read_training_preferences(first), original)
        self.assertIsNone(read_training_preferences(second))
        changed = validate_training_preferences("advanced", "very_active", ["weight_machines", "barbell"], [7, 2], 180)
        save_training_preferences(first, changed)
        self.assertEqual(read_training_preferences(first), changed)
        self.assertIsNone(read_training_preferences(second))

    def test_concurrent_retries_create_one_record(self):
        owner = self.owner()
        details = validate_training_preferences("intermediate", "lightly_active", ["bench"], [1, 3], 45)
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: save_training_preferences(owner, details), range(2)))
        self.assertEqual(results, [details, details])
        with session_scope() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(TrainingPreferences)
                                           .where(TrainingPreferences.user_id == owner)), 1)

    def test_database_rejects_invalid_values_and_missing_profile(self):
        owner = self.owner()
        valid = dict(user_id=owner, experience="beginner", activity="mostly_seated",
                     equipment_mask=0, weekday_mask=1, session_minutes=30)
        for changes in [dict(experience="expert"), dict(activity="unknown"), dict(equipment_mask=-1),
                        dict(equipment_mask=128), dict(weekday_mask=0), dict(weekday_mask=128),
                        dict(session_minutes=9), dict(session_minutes=181), dict(user_id=uuid4())]:
            with self.subTest(changes=changes), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(TrainingPreferences(**(valid | changes)))
        self.assertIsNone(read_training_preferences(owner))

    def test_migration_matches_registered_models(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base, get_engine
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
