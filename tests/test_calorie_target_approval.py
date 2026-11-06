"""Approval is atomic, owner-scoped, stale-safe, and idempotent."""

from concurrent.futures import ThreadPoolExecutor
import os
import unittest
from uuid import uuid4

from sqlalchemy import select

from backend.accounts import register_account
from backend.calorie_proposals import create_calorie_proposal
from backend.calorie_targets import (CalorieProposalNotFound, StaleCalorieProposal,
                                     approve_calorie_proposal, read_active_calorie_target)
from backend.database import close_database, session_scope
from backend.energy_preferences import save_energy_preferences
from backend.goals import save_goal
from backend.models import CalorieProposal, CalorieTargetVersion
from backend.profiles import save_profile
from backend.services.energy_preferences import validate_energy_preferences
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CalorieTargetApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self):
        identity = register_account("target_approve_" + uuid4().hex[:12], "synthetic proposal password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
        save_goal(identity.user_id, "gain", 75)
        save_energy_preferences(identity.user_id, validate_energy_preferences("male", "inactive", "general_adult"))
        return identity.user_id

    def test_explicit_versions_preserve_history_and_retries_do_not_reactivate(self):
        owner, other = self.owner(), self.owner()
        self.assertIsNone(read_active_calorie_target(owner))
        first = create_calorie_proposal(owner, 100)
        competing = create_calorie_proposal(owner, 200)
        with self.assertRaises(CalorieProposalNotFound):
            approve_calorie_proposal(other, first.id)
        approved = approve_calorie_proposal(owner, first.id)
        self.assertEqual((approved.version, approved.status, approved.proposal_id), (1, "active", first.id))
        self.assertEqual(read_active_calorie_target(owner), approved)
        self.assertEqual(approve_calorie_proposal(owner, first.id), approved)
        with self.assertRaises(StaleCalorieProposal):
            approve_calorie_proposal(owner, competing.id)
        second = create_calorie_proposal(owner, 200)
        self.assertEqual(second.base_version_id, approved.id)
        replacement = approve_calorie_proposal(owner, second.id)
        self.assertEqual((replacement.version, replacement.status), (2, "active"))
        self.assertEqual(read_active_calorie_target(owner), replacement)
        old_retry = approve_calorie_proposal(owner, first.id)
        self.assertEqual((old_retry.id, old_retry.status, old_retry.version),
                         (approved.id, "superseded", 1))
        self.assertEqual(read_active_calorie_target(owner), replacement)
        with session_scope() as session:
            rows = session.scalars(select(CalorieTargetVersion).where(
                CalorieTargetVersion.user_id == owner,
            ).order_by(CalorieTargetVersion.version)).all()
            self.assertEqual([(row.version, row.status) for row in rows],
                             [(1, "superseded"), (2, "active")])
            self.assertIsNotNone(rows[0].superseded_at)
            self.assertEqual(session.get(CalorieProposal, competing.id).status, "pending")
            self.assertEqual(session.get(CalorieProposal, first.id).status, "approved")

    def test_changed_sources_reject_without_activation(self):
        for change in ("weight", "goal", "energy"):
            with self.subTest(change=change):
                owner = self.owner()
                proposal = create_calorie_proposal(owner, 100)
                if change == "weight":
                    save_profile(owner, validate_profile(30, 175, 71, "UTC"))
                elif change == "goal":
                    save_goal(owner, "gain", 76)
                else:
                    save_energy_preferences(owner, validate_energy_preferences("male", "low_active", "general_adult"))
                with self.assertRaises(StaleCalorieProposal):
                    approve_calorie_proposal(owner, proposal.id)
                self.assertIsNone(read_active_calorie_target(owner))
                with session_scope() as session:
                    self.assertEqual(session.get(CalorieProposal, proposal.id).status, "pending")

    def test_concurrent_retries_create_one_version(self):
        owner = self.owner()
        proposal = create_calorie_proposal(owner, 100)
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: approve_calorie_proposal(owner, proposal.id), range(2)))
        self.assertEqual(results[0].id, results[1].id)
        with session_scope() as session:
            rows = session.scalars(select(CalorieTargetVersion).where(
                CalorieTargetVersion.user_id == owner,
            )).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].status, "active")
