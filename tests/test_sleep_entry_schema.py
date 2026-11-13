"""PostgreSQL constrains owner-local sleep dates and explicit minutes."""

from datetime import date
import os
import unittest
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import session_scope
from backend.models import Profile, SleepEntry
from backend.profiles import save_profile
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class SleepEntrySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def owner(self):
        identity = register_account("sleep_schema_" + uuid4().hex[:12], "synthetic sleep password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        return identity.user_id

    def test_unique_date_bounds_and_profile_cascade(self):
        first, second = self.owner(), self.owner()
        day = date(2026, 11, 13)
        with session_scope() as session:
            session.add_all((SleepEntry(user_id=first, local_date=day, sleep_minutes=0),
                             SleepEntry(user_id=second, local_date=day, sleep_minutes=1440)))
        for values in ({"user_id": first, "local_date": day, "sleep_minutes": 450},
                       {"user_id": first, "local_date": date(2026, 11, 12), "sleep_minutes": -1},
                       {"user_id": first, "local_date": date(2026, 11, 12), "sleep_minutes": 1441},
                       {"user_id": uuid4(), "local_date": day, "sleep_minutes": 450}):
            with self.subTest(values=values), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(SleepEntry(**values))
        with session_scope() as session:
            session.execute(delete(Profile).where(Profile.user_id == first))
            self.assertEqual(session.scalar(select(func.count()).select_from(SleepEntry)
                                            .where(SleepEntry.user_id == first)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(SleepEntry)
                                            .where(SleepEntry.user_id == second)), 1)

    def test_migration_matches_models(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base, get_engine
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
