"""Sleep observations stay private, correctable, and separate from the profile."""

from datetime import date, datetime, timedelta, timezone
import os
import unittest
from uuid import uuid4

from backend.accounts import register_account
from backend.profiles import read_profile, save_profile
from backend.services.profiles import validate_profile
from backend.services.sleep_entries import InvalidSleepEntry, SleepEntryDetails
from backend.sleep_entries import SleepProfileRequired, list_recent_sleep_entries, save_sleep_entry
import test_accounts_database as database_tests


@unittest.skipUnless(os.environ.get("TRAINAI_TEST_DATABASE_URL"), "Disposable PostgreSQL not configured")
class SleepEntryStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_tests.AccountDatabaseTests.setUpClass()

    def owner(self, zone="UTC"):
        identity = register_account("sleep_store_" + uuid4().hex[:12], "synthetic sleep password")
        save_profile(identity.user_id, validate_profile(30, 175, 70, zone))
        return identity.user_id

    def test_owner_date_correction_zero_and_profile_separation(self):
        first, second = self.owner(), self.owner()
        now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
        day = date(2026, 11, 13)
        original = SleepEntryDetails(day, 420)
        self.assertEqual(save_sleep_entry(first, original, now), original)
        self.assertEqual(list_recent_sleep_entries(second), ())
        corrected = SleepEntryDetails(day, 0)
        self.assertEqual(save_sleep_entry(first, corrected, now), corrected)
        self.assertEqual(list_recent_sleep_entries(first), (corrected,))
        self.assertEqual(read_profile(first).weight_kg, 70)

    def test_local_date_boundary_and_invalid_update_preserves_row(self):
        seoul, utc = self.owner("Asia/Seoul"), self.owner("UTC")
        now = datetime(2026, 11, 12, 15, 30, tzinfo=timezone.utc)
        entry = SleepEntryDetails(date(2026, 11, 13), 450)
        self.assertEqual(save_sleep_entry(seoul, entry, now), entry)
        with self.assertRaises(InvalidSleepEntry):
            save_sleep_entry(utc, entry, now)
        with self.assertRaises(InvalidSleepEntry):
            save_sleep_entry(seoul, SleepEntryDetails(entry.local_date, 1441), now)
        self.assertEqual(list_recent_sleep_entries(seoul), (entry,))
        save_profile(seoul, validate_profile(30, 175, 70, "UTC"))
        self.assertEqual(list_recent_sleep_entries(seoul), (entry,))

    def test_profile_first_and_bounded_recent_list(self):
        identity = register_account("sleep_store_" + uuid4().hex[:12], "synthetic sleep password")
        now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
        with self.assertRaises(SleepProfileRequired):
            save_sleep_entry(identity.user_id, SleepEntryDetails(now.date(), 450), now)
        owner = self.owner()
        for offset in range(34):
            save_sleep_entry(owner, SleepEntryDetails(now.date() - timedelta(days=offset), 400 + offset), now)
        recent = list_recent_sleep_entries(owner)
        self.assertEqual(len(recent), 30)
        self.assertEqual(recent[0].local_date, now.date())
        self.assertEqual(recent[-1].local_date, now.date() - timedelta(days=29))
