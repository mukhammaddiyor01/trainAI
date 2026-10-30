"""Goal ownership, snapshot stability, retries, and actual PostgreSQL constraints."""

from concurrent.futures import ThreadPoolExecutor
import os
import unittest
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.goals import GoalProfileRequired, read_goal, save_goal
from backend.models import Goal
from backend.profiles import save_profile
from backend.services.goals import GoalDetails, InvalidGoal
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class GoalStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def account(self, weight=None):
        identity = register_account("goal_" + uuid4().hex[:20], "synthetic test passphrase")
        if weight is not None:
            save_profile(identity.user_id, validate_profile(30, 175, weight, "UTC"))
        return identity.user_id

    def test_profile_is_required_and_goals_are_owner_scoped(self):
        missing = self.account()
        with self.assertRaises(GoalProfileRequired):
            save_goal(missing, "gain", 75)
        first, second = self.account(60), self.account(70)
        self.assertEqual(save_goal(first, "gain", 75), GoalDetails("gain", 60, 75))
        self.assertIsNone(read_goal(second))

    def test_profile_edits_and_retries_preserve_existing_snapshot(self):
        owner = self.account(60)
        original = save_goal(owner, "gain", 75)
        save_profile(owner, validate_profile(30, 175, 76, "UTC"))
        self.assertEqual(read_goal(owner), original)
        self.assertEqual(save_goal(owner, "gain", 75), original)
        changed = save_goal(owner, "lose", 70)
        self.assertEqual(changed, GoalDetails("lose", 76, 70))
        with self.assertRaises(InvalidGoal):
            save_goal(owner, "gain", 70)
        self.assertEqual(read_goal(owner), changed)

    def test_concurrent_identical_saves_keep_one_goal(self):
        owner = self.account(60)
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: save_goal(owner, "gain", 75), range(2)))
        self.assertEqual(results[0], results[1])
        with session_scope() as session:
            count = session.scalar(select(func.count()).select_from(Goal).where(Goal.user_id == owner))
        self.assertEqual(count, 1)

    def test_database_rejects_invalid_shapes_and_missing_profile_foreign_key(self):
        owner = self.account(60)
        cases = [(owner, "gain", 60, None), (owner, "lose", 60, 65),
                 (owner, "maintain", 60, 60), (uuid4(), "maintain", 60, None)]
        for user_id, direction, starting, target in cases:
            with self.subTest(direction=direction), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(Goal(user_id=user_id, direction=direction,
                                     starting_weight_kg=starting, target_weight_kg=target))

    def test_migration_matches_registered_models(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base, get_engine
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
