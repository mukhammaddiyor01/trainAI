"""Readiness inputs are one owner-scoped snapshot without inferred answers."""

import os
import unittest
from uuid import uuid4

from backend.accounts import register_account
from backend.database import close_database
from backend.exercise_readiness import read_exercise_readiness_inputs
from backend.movement_limitations import save_movement_limitations
from backend.profiles import save_profile
from backend.services.movement_limitations import validate_movement_limitations
from backend.services.profiles import validate_profile
from backend.services.training_preferences import validate_training_preferences
from backend.training_preferences import save_training_preferences
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class ExerciseReadinessStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        return register_account("readiness_" + uuid4().hex[:20], "synthetic test passphrase").user_id

    def test_profile_first_and_missing_answers_stay_missing(self):
        owner = self.owner()
        self.assertIsNone(read_exercise_readiness_inputs(owner))
        save_profile(owner, validate_profile(30, 175, 70, "UTC"))
        self.assertEqual(read_exercise_readiness_inputs(owner), (None, None))

    def test_owner_snapshot_keeps_complete_selections_isolated(self):
        first, second = self.owner(), self.owner()
        for owner in (first, second):
            save_profile(owner, validate_profile(30, 175, 70, "UTC"))
        preferences = validate_training_preferences(
            "beginner", "mostly_seated", ["bench", "dumbbells"], [7, 1, 3], 40,
        )
        limitations = validate_movement_limitations("needs_adaptation")
        save_training_preferences(first, preferences)
        save_movement_limitations(first, limitations)
        self.assertEqual(read_exercise_readiness_inputs(first), (preferences, limitations))
        self.assertEqual(read_exercise_readiness_inputs(second), (None, None))
