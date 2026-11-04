"""Pending proposals use current owner inputs and never activate a target."""

from dataclasses import FrozenInstanceError
import os
import unittest
from uuid import uuid4

from sqlalchemy import func, select

from backend.accounts import register_account
from backend.calorie_proposals import CalorieProposalInputsRequired, create_calorie_proposal, read_calorie_proposal
from backend.database import close_database, session_scope
from backend.energy_preferences import save_energy_preferences
from backend.goals import save_goal
from backend.models import CalorieProposal, EnergyPreferences, Goal
from backend.profiles import save_profile
from backend.services.calorie_preview import CaloriePreviewUnavailable, InvalidCalorieAdjustment
from backend.services.energy_preferences import validate_energy_preferences
from backend.services.profiles import validate_profile
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class CalorieProposalStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self, *, complete=True):
        identity = register_account("proposal_store_" + uuid4().hex[:12], "synthetic proposal password")
        if complete:
            save_profile(identity.user_id, validate_profile(30, 175, 70, "UTC"))
            save_goal(identity.user_id, "gain", 75)
            save_energy_preferences(identity.user_id, validate_energy_preferences("male", "inactive", "general_adult"))
        return identity.user_id

    def count(self, owner):
        with session_scope() as session:
            return session.scalar(select(func.count()).select_from(CalorieProposal)
                                  .where(CalorieProposal.user_id == owner))

    def test_current_snapshot_is_private_pending_and_immutable(self):
        first, second = self.owner(), self.owner()
        proposal = create_calorie_proposal(first, 200)
        self.assertEqual(proposal.status, "pending")
        self.assertEqual(proposal.user_id, first)
        self.assertEqual((proposal.profile_weight_kg, proposal.goal_starting_weight_kg), (70, 70))
        self.assertAlmostEqual(proposal.maintenance_kcal_per_day, 2552.67)
        self.assertAlmostEqual(proposal.preview_kcal_per_day, 2752.67)
        self.assertIsNotNone(proposal.created_at)
        self.assertEqual(read_calorie_proposal(first, proposal.id), proposal)
        self.assertIsNone(read_calorie_proposal(second, proposal.id))
        with self.assertRaises(FrozenInstanceError):
            proposal.status = "approved"
        with session_scope() as session:
            self.assertEqual(session.get(Goal, first).direction, "gain")
            self.assertEqual(session.get(EnergyPreferences, first).equation_sex, "male")
        self.assertEqual(self.count(first), 1)
        self.assertEqual(self.count(second), 0)

    def test_missing_or_invalid_inputs_leave_no_row(self):
        owner = self.owner(complete=False)
        with self.assertRaises(CalorieProposalInputsRequired):
            create_calorie_proposal(owner, 200)
        save_profile(owner, validate_profile(30, 175, 70, "UTC"))
        with self.assertRaises(CalorieProposalInputsRequired):
            create_calorie_proposal(owner, 200)
        save_goal(owner, "gain", 75)
        save_energy_preferences(owner, validate_energy_preferences("male", "inactive", "general_adult"))
        for amount in (0, 251, True):
            with self.subTest(amount=amount), self.assertRaises(InvalidCalorieAdjustment):
                create_calorie_proposal(owner, amount)
        save_profile(owner, validate_profile(30, 175, 75, "UTC"))
        with self.assertRaises(CaloriePreviewUnavailable):
            create_calorie_proposal(owner, 200)
        self.assertEqual(self.count(owner), 0)

    def test_new_proposal_recomputes_changed_weight_without_rewriting_old_snapshot(self):
        owner = self.owner()
        first = create_calorie_proposal(owner, 100)
        save_profile(owner, validate_profile(30, 175, 72, "UTC"))
        second = create_calorie_proposal(owner, 100)
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.profile_weight_kg, 70)
        self.assertEqual(second.profile_weight_kg, 72)
        self.assertEqual(second.goal_starting_weight_kg, 70)
        self.assertAlmostEqual(second.maintenance_kcal_per_day, 2580.87)
        self.assertEqual(read_calorie_proposal(owner, first.id), first)
        self.assertEqual(self.count(owner), 2)
