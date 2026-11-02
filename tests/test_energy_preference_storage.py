"""Energy preferences require a profile and remain private, complete, and strictly constrained."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from itertools import product
import os
import unittest
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.energy_preferences import read_energy_preferences, save_energy_preferences
from backend.models import EnergyPreferences, Profile
from backend.profiles import save_profile
from backend.services.profiles import validate_profile
from backend.services.energy_preferences import (
    ENERGY_ACTIVITY_CATEGORIES, ENERGY_CONTEXTS, EQUATION_SEX_OPTIONS,
    InvalidEnergyPreferences, validate_energy_preferences,
)
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class EnergyPreferenceStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("energy_" + uuid4().hex[:18], "synthetic energy password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        return identity.user_id

    def test_all_choices_round_trip_without_backfill_or_cross_owner_changes(self):
        first, second = self.owner(), self.owner()
        self.assertIsNone(read_energy_preferences(first))
        for values in product(EQUATION_SEX_OPTIONS, ENERGY_ACTIVITY_CATEGORIES, ENERGY_CONTEXTS):
            details = validate_energy_preferences(*values)
            self.assertEqual(save_energy_preferences(first, details), details)
            self.assertEqual(read_energy_preferences(first), details)
            self.assertIsNone(read_energy_preferences(second))
        with self.assertRaises(InvalidEnergyPreferences):
            save_energy_preferences(first, replace(details, context="invalid"))
        self.assertEqual(read_energy_preferences(first), details)

    def test_concurrent_updates_keep_one_complete_selection(self):
        owner = self.owner()
        options = [validate_energy_preferences("male", "active", "general_adult"),
                   validate_energy_preferences("unsure", "inactive", "clinical")]
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda details: save_energy_preferences(owner, details), options))
        self.assertEqual(results, options)
        self.assertIn(read_energy_preferences(owner), options)
        with session_scope() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(EnergyPreferences)
                                           .where(EnergyPreferences.user_id == owner)), 1)

    def test_sql_choices_nulls_missing_profiles_and_cascade(self):
        owner = self.owner()
        valid = dict(user_id=owner, equation_sex="male", activity_category="active", context="general_adult")
        for change in [dict(equation_sex="other"), dict(equation_sex=None), dict(activity_category="mostly_seated"),
                       dict(activity_category=None), dict(context="healthy"), dict(context=None), dict(user_id=uuid4())]:
            with self.subTest(change=change), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(EnergyPreferences(**(valid | change)))
        self.assertIsNone(read_energy_preferences(owner))
        save_energy_preferences(owner, validate_energy_preferences("unsure", "unsure", "unsure"))
        with session_scope() as session:
            session.execute(delete(Profile).where(Profile.user_id == owner))
        self.assertIsNone(read_energy_preferences(owner))

    def test_migration_matches_models(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base, get_engine
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
