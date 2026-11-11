"""Owner-local weight dates are unique and constrained in PostgreSQL."""

from datetime import date
import os
import unittest
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.models import Profile, WeightEntry
from backend.profiles import save_profile
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WeightEntrySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("weight_schema_" + uuid4().hex[:12], "synthetic weight password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        return identity.user_id

    def test_owner_date_uniqueness_bounds_and_cascade(self):
        first, second = self.owner(), self.owner()
        day = date(2026, 11, 11)
        with session_scope() as session:
            session.add_all((WeightEntry(user_id=first, local_date=day, weight_kg=70),
                             WeightEntry(user_id=second, local_date=day, weight_kg=71)))
        with session_scope() as session:
            row = session.get(WeightEntry, (first, day))
            self.assertIsNotNone(row.created_at)
            self.assertIsNotNone(row.updated_at)
        for changes in ({"user_id": first, "local_date": day, "weight_kg": 72},
                        {"user_id": first, "local_date": date(2026, 11, 10), "weight_kg": 19},
                        {"user_id": first, "local_date": date(2026, 11, 10), "weight_kg": 501},
                        {"user_id": uuid4(), "local_date": day, "weight_kg": 70}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(WeightEntry(**changes))
        with session_scope() as session:
            session.execute(delete(Profile).where(Profile.user_id == first))
            self.assertEqual(session.scalar(select(func.count()).select_from(WeightEntry)
                                            .where(WeightEntry.user_id == first)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(WeightEntry)
                                            .where(WeightEntry.user_id == second)), 1)

    def test_migration_matches_models(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base, get_engine
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
