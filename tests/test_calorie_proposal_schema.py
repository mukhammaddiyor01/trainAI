"""Pending proposal rows are owner-scoped and constrained before APIs exist."""

import os
import unittest
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.accounts import register_account
from backend.database import close_database, session_scope
from backend.models import CalorieProposal
from backend.profiles import save_profile
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CalorieProposalSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("proposal_schema_" + uuid4().hex[:12], "synthetic proposal password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        return identity.user_id

    def valid_row(self, owner):
        return dict(user_id=owner, status="pending", profile_age=30, profile_height_cm=175,
                    profile_weight_kg=70, goal_direction="gain", goal_starting_weight_kg=70,
                    goal_target_weight_kg=75, equation_sex="male", activity_category="inactive",
                    context="general_adult", adjustment_kcal=200, signed_adjustment_kcal=200,
                    maintenance_kcal_per_day=2552.67, preview_kcal_per_day=2752.67,
                    energy_method_version="dri-2023-adult-eer-v1",
                    policy_version="manual-adjustment-preview-2026-11-04-v1")

    def test_pending_owner_row(self):
        owner = self.owner()
        with session_scope() as session:
            session.add(CalorieProposal(**self.valid_row(owner)))
        with session_scope() as session:
            row = session.scalar(select(CalorieProposal).where(CalorieProposal.user_id == owner))
            self.assertEqual(row.status, "pending")
            self.assertEqual(row.preview_kcal_per_day, 2752.67)
            self.assertIsNotNone(row.id)
            self.assertIsNotNone(row.created_at)

    def test_sql_rejects_forged_status_magnitude_versions_and_missing_owner(self):
        owner = self.owner()
        for change in (dict(status="approved"), dict(adjustment_kcal=251),
                       dict(signed_adjustment_kcal=-200), dict(context="clinical"),
                       dict(goal_target_weight_kg=None),
                       dict(policy_version="unreviewed"), dict(user_id=uuid4())):
            with self.subTest(change=change), self.assertRaises(IntegrityError):
                with session_scope() as session:
                    session.add(CalorieProposal(**(self.valid_row(owner) | change)))
        with session_scope() as session:
            self.assertIsNone(session.scalar(select(CalorieProposal).where(CalorieProposal.user_id == owner)))
