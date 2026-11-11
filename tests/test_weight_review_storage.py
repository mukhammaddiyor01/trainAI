"""A weekly read uses the owner's saved zone and all 35 possible dates."""

from datetime import date, datetime, timedelta, timezone
import os
import unittest
from uuid import uuid4

from backend.accounts import register_account
from backend.profiles import save_profile
from backend.services.profiles import validate_profile
from backend.services.weight_entries import WeightEntryDetails
from backend.weight_entries import read_weight_review, save_weight_entry
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class WeightReviewStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def owner(self, zone):
        identity = register_account("review_store_" + uuid4().hex[:12], "synthetic review password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, zone))
        return identity.user_id

    def test_all_five_weeks_and_owner_isolation(self):
        first, second = self.owner("UTC"), self.owner("UTC")
        now = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
        oldest_monday = date(2026, 10, 12)
        for offset in range(31):
            day = oldest_monday + timedelta(days=offset)
            save_weight_entry(first, WeightEntryDetails(day, 70 + offset / 10), now)
        own = read_weight_review(first, now)
        other = read_weight_review(second, now)
        self.assertEqual(sum(week.observed_dates for week in own), 31)
        self.assertEqual(own[-1].week_start, oldest_monday)
        self.assertEqual(own[-1].first.local_date, oldest_monday)
        self.assertTrue(all(week.observed_dates == 0 for week in other))
        self.assertIsNone(read_weight_review(uuid4(), now))

    def test_owner_local_today_and_correction_are_reflected(self):
        seoul, utc = self.owner("Asia/Seoul"), self.owner("UTC")
        now = datetime(2026, 11, 8, 15, 30, tzinfo=timezone.utc)
        seoul_day = date(2026, 11, 9)
        save_weight_entry(seoul, WeightEntryDetails(seoul_day, 70), now)
        save_weight_entry(seoul, WeightEntryDetails(seoul_day, 70.5), now)
        self.assertEqual(read_weight_review(seoul, now)[0].week_start, seoul_day)
        self.assertEqual(read_weight_review(seoul, now)[0].first.weight_kg, 70.5)
        self.assertEqual(read_weight_review(utc, now)[0].week_start, date(2026, 11, 2))
        with self.assertRaises(ValueError):
            read_weight_review(seoul, datetime(2026, 11, 9))
