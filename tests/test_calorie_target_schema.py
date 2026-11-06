"""SQL constraints protect target-version ownership and one active row."""

from datetime import datetime, timezone
import os
import unittest
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.calorie_proposals import create_calorie_proposal
from backend.database import close_database, session_scope
from backend.energy_preferences import save_energy_preferences
from backend.goals import save_goal
from backend.models import CalorieProposal, CalorieTargetVersion
from backend.profiles import save_profile
from backend.services.energy_preferences import validate_energy_preferences
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CalorieTargetSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("target_schema_" + uuid4().hex[:12], "synthetic proposal password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        save_goal(identity.user_id, "gain", 75)
        save_energy_preferences(identity.user_id, validate_energy_preferences("male", "inactive", "general_adult"))
        return identity.user_id

    def test_pending_proposals_and_version_constraints(self):
        first, second = self.owner(), self.owner()
        proposal = create_calorie_proposal(first, 100)
        other = create_calorie_proposal(second, 100)
        with session_scope() as session:
            row = session.get(CalorieProposal, proposal.id)
            self.assertEqual((row.status, row.approved_at, row.base_version_id), ("pending", None, None))
        now = datetime.now(timezone.utc)
        for values in (
            dict(user_id=second, proposal_id=proposal.id, version=1, status="active", target_kcal_per_day=2600),
            dict(user_id=first, proposal_id=uuid4(), version=1, status="active", target_kcal_per_day=2600),
            dict(user_id=first, proposal_id=proposal.id, version=0, status="active", target_kcal_per_day=2600),
            dict(user_id=first, proposal_id=proposal.id, version=1, status="active", target_kcal_per_day=1499),
            dict(user_id=first, proposal_id=proposal.id, version=1, status="superseded", target_kcal_per_day=2600),
        ):
            with self.subTest(values=values), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(CalorieTargetVersion(**values))
        with session_scope() as session:
            session.add(CalorieTargetVersion(user_id=first, proposal_id=proposal.id, version=1,
                                             status="active", target_kcal_per_day=proposal.preview_kcal_per_day))
            row = session.get(CalorieProposal, proposal.id)
            row.status = "approved"
            row.approved_at = now
        next_proposal = create_calorie_proposal(first, 100)
        with session_scope() as session:
            active = session.scalar(select(CalorieTargetVersion).where(CalorieTargetVersion.user_id == first))
            self.assertEqual(next_proposal.base_version_id, active.id)
        for values in (
            dict(user_id=first, proposal_id=next_proposal.id, version=2, status="active",
                 target_kcal_per_day=next_proposal.preview_kcal_per_day),
            dict(user_id=first, proposal_id=next_proposal.id, version=1, status="superseded",
                 target_kcal_per_day=next_proposal.preview_kcal_per_day, superseded_at=now),
            dict(user_id=first, proposal_id=proposal.id, version=2, status="superseded",
                 target_kcal_per_day=proposal.preview_kcal_per_day, superseded_at=now),
        ):
            with self.subTest(values=values), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(CalorieTargetVersion(**values))
        with session_scope() as session:
            rows = session.scalars(select(CalorieTargetVersion).where(CalorieTargetVersion.user_id == first)).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].status, "active")
            self.assertIsNone(session.scalar(select(CalorieTargetVersion).where(CalorieTargetVersion.user_id == second)))
            self.assertEqual(session.get(CalorieProposal, other.id).status, "pending")
