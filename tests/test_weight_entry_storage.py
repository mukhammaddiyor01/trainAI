"""Dated observations stay owner-scoped and do not rewrite planning inputs."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import os
import unittest
from uuid import uuid4

from backend.accounts import register_account
from backend.database import close_database
from backend.goals import read_goal, save_goal
from backend.profiles import read_profile, save_profile
from backend.services.profiles import validate_profile
from backend.services.weight_entries import InvalidWeightEntry, WeightEntryDetails
from backend.weight_entries import WeightProfileRequired, list_recent_weight_entries, save_weight_entry
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WeightEntryStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_database()

    def owner(self, zone="UTC"):
        identity = register_account("weight_store_" + uuid4().hex[:12], "synthetic weight password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, zone))
        return identity.user_id

    def test_owner_date_correction_and_plan_inputs_remain_separate(self):
        first, second = self.owner(), self.owner()
        save_goal(first, "gain", 75)
        now = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
        day = date(2026, 11, 11)
        original = WeightEntryDetails(day, 71)
        self.assertEqual(save_weight_entry(first, original, now), original)
        self.assertEqual(list_recent_weight_entries(first), (original,))
        self.assertEqual(list_recent_weight_entries(second), ())
        corrected = WeightEntryDetails(day, 70.5)
        self.assertEqual(save_weight_entry(first, corrected, now), corrected)
        self.assertEqual(list_recent_weight_entries(first), (corrected,))
        self.assertEqual(read_profile(first).weight_kg, 70)
        self.assertEqual(read_goal(first).starting_weight_kg, 70)

    def test_local_date_boundary_and_invalid_change_preserve_prior_row(self):
        seoul, utc = self.owner("Asia/Seoul"), self.owner("UTC")
        now = datetime(2026, 11, 10, 15, 30, tzinfo=timezone.utc)
        next_local_day = WeightEntryDetails(date(2026, 11, 11), 70)
        self.assertEqual(save_weight_entry(seoul, next_local_day, now), next_local_day)
        with self.assertRaises(InvalidWeightEntry):
            save_weight_entry(utc, next_local_day, now)
        with self.assertRaises(InvalidWeightEntry):
            save_weight_entry(seoul, replace(next_local_day, weight_kg=500.1), now)
        with self.assertRaises(ValueError):
            save_weight_entry(seoul, next_local_day, datetime(2026, 11, 10, 15, 30))
        self.assertEqual(list_recent_weight_entries(seoul), (next_local_day,))
        self.assertEqual(list_recent_weight_entries(utc), ())
        save_profile(seoul, validate_profile(30, 175, 70, "UTC"))
        self.assertEqual(list_recent_weight_entries(seoul), (next_local_day,))

    def test_missing_profile_and_bounded_newest_first_read(self):
        identity = register_account("weight_store_" + uuid4().hex[:12], "synthetic weight password")
        now = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
        with self.assertRaises(WeightProfileRequired):
            save_weight_entry(identity.user_id, WeightEntryDetails(date(2026, 11, 11), 70), now)
        owner = self.owner()
        for offset in range(34):
            day = now.date() - timedelta(days=offset)
            save_weight_entry(owner, WeightEntryDetails(day, 70 + offset / 10), now)
        recent = list_recent_weight_entries(owner)
        self.assertEqual(len(recent), 30)
        self.assertEqual(recent[0].local_date, now.date())
        self.assertEqual(recent[-1].local_date, now.date() - timedelta(days=29))
