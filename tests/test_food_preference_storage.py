"""Food preferences are private, atomic, bounded, and migration-backed."""

from concurrent.futures import ThreadPoolExecutor
import os
import unittest
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.food_preferences import read_food_preferences, save_food_preferences
from backend.models import FoodPreferences
from backend.profiles import save_profile
from backend.services.profiles import validate_profile
from backend.services.food_preferences import validate_food_preferences, FoodPreferencesDetails, InvalidFoodPreferences
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class FoodPreferenceStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("food_" + uuid4().hex[:20], "synthetic food password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        return identity.user_id

    def details(self):
        return validate_food_preferences("mixed", "listed", ["Sesame", "Milk"], "economical", 0, ["23:59", "00:00"])

    def test_round_trip_and_full_replacement_remain_private(self):
        first, second = self.owner(), self.owner()
        self.assertIsNone(read_food_preferences(first))
        original = self.details()
        save_food_preferences(first, original)
        self.assertEqual(read_food_preferences(first), original)
        self.assertIsNone(read_food_preferences(second))
        changed = validate_food_preferences("vegan", "unsure", [], "flexible", 180, ["08:00"])
        save_food_preferences(first, changed)
        self.assertEqual(read_food_preferences(first), changed)
        with self.assertRaises(InvalidFoodPreferences):
            save_food_preferences(first, FoodPreferencesDetails("vegan", "none_reported", ("milk",), "flexible", 0, ("08:00",)))
        self.assertEqual(read_food_preferences(first), changed)
        self.assertIsNone(read_food_preferences(second))

    def test_concurrent_retries_keep_one_complete_row(self):
        owner, details = self.owner(), self.details()
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: save_food_preferences(owner, details), range(2)))
        self.assertEqual(results, [details, details])
        self.assertEqual(read_food_preferences(owner), details)
        with session_scope() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(FoodPreferences)
                                           .where(FoodPreferences.user_id == owner)), 1)

    def test_sql_bounds_allergy_consistency_and_profile_foreign_key(self):
        owner = self.owner()
        valid = dict(user_id=owner, diet="mixed", allergy_status="none_reported", allergies=[],
                     budget_level="economical", prep_minutes=0, meal_minutes=[480])
        changes = [dict(diet="unknown"), dict(allergy_status="unknown"), dict(allergy_status="listed"),
                   dict(allergies=["milk"]), dict(allergies=[None]), dict(allergies=None),
                   dict(allergy_status="listed", allergies=["x"] * 21), dict(budget_level="unknown"),
                   dict(prep_minutes=-1), dict(prep_minutes=181), dict(meal_minutes=[]),
                   dict(meal_minutes=[0] * 9), dict(meal_minutes=[None]), dict(meal_minutes=[1440]),
                   dict(meal_minutes=[-1]), dict(user_id=uuid4())]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(FoodPreferences(**(valid | change)))
        self.assertIsNone(read_food_preferences(owner))

    def test_migration_matches_models(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base, get_engine
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
