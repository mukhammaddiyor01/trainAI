"""Movement limitation answers remain private, explicit, and SQL constrained."""

from concurrent.futures import ThreadPoolExecutor
import os
import unittest
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.models import MovementLimitations, Profile
from backend.movement_limitations import read_movement_limitations, save_movement_limitations
from backend.profiles import save_profile
from backend.services.movement_limitations import validate_movement_limitations
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class MovementLimitationStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("movement_" + uuid4().hex[:18], "synthetic movement password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        return identity.user_id

    def test_absent_is_unknown_and_saves_are_owner_scoped(self):
        first, second = self.owner(), self.owner()
        self.assertIsNone(read_movement_limitations(first))
        self.assertIsNone(read_movement_limitations(second))
        for status in ("unsure", "needs_adaptation", "none_reported"):
            details = validate_movement_limitations(status)
            self.assertEqual(save_movement_limitations(first, details), details)
            self.assertEqual(read_movement_limitations(first), details)
            self.assertIsNone(read_movement_limitations(second))

    def test_retries_keep_one_row_and_sql_rejects_invalid_values(self):
        owner = self.owner()
        details = validate_movement_limitations("needs_adaptation")
        with ThreadPoolExecutor(max_workers=2) as workers:
            self.assertEqual(list(workers.map(lambda _: save_movement_limitations(owner, details), range(2))),
                             [details, details])
        with session_scope() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(MovementLimitations)
                                           .where(MovementLimitations.user_id == owner)), 1)
        for changes in ({"status": "cleared"}, {"status": None}, {"user_id": uuid4()}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(MovementLimitations(**({"user_id": self.owner(), "status": "unsure"} | changes)))
        with session_scope() as session:
            session.execute(delete(Profile).where(Profile.user_id == owner))
        self.assertIsNone(read_movement_limitations(owner))

    def test_migration_matches_models(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base, get_engine
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
