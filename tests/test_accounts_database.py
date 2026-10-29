"""Run only against an explicit disposable PostgreSQL test database."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from backend.database import close_database, get_engine, session_scope
from backend.models import LoginSession, User


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class AccountDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_url = os.environ["TRAINAI_TEST_DATABASE_URL"]
        if test_url != os.environ.get("DATABASE_URL"):
            raise RuntimeError("Test and application URLs must match in the isolated test process.")
        from sqlalchemy.engine import make_url
        if not (make_url(test_url).database or "").endswith("_test"):
            raise RuntimeError("Integration tests require a database name ending in _test.")
        close_database()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def test_migrations_match_model_metadata(self):
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from backend.database import Base
        with get_engine().connect() as connection:
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
        self.assertIn("users", inspect(get_engine()).get_table_names())

    def test_transactions_commit_and_roll_back(self):
        username = "test_" + uuid4().hex[:20]
        with session_scope() as session:
            user = User(username=username, password_hash="synthetic-hash")
            session.add(user)
            session.flush()
            user_id = user.id
        with self.assertRaisesRegex(ValueError, "Abort"):
            with session_scope() as session:
                session.add(User(username="rollback_" + uuid4().hex[:20], password_hash="synthetic-hash"))
                session.flush()
                raise ValueError("Abort")
        with session_scope() as session:
            self.assertIsNotNone(session.get(User, user_id))
            self.assertIsNone(session.scalar(select(User).where(User.username.like("rollback_%"))))

    def test_username_uniqueness_and_session_foreign_key(self):
        username = "unique_" + uuid4().hex[:20]
        with session_scope() as session:
            session.add(User(username=username, password_hash="synthetic-hash"))
        with self.assertRaises(IntegrityError):
            with session_scope() as session:
                session.add(User(username=username, password_hash="synthetic-hash"))
        with self.assertRaises(IntegrityError):
            with session_scope() as session:
                session.add(LoginSession(token_digest=uuid4().hex * 2, user_id=uuid4(),
                                         expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))


if __name__ == "__main__":
    unittest.main()
