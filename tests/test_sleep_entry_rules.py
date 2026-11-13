"""Sleep duration is an explicit, bounded observation without interpretation."""

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta
import unittest

from backend.services.sleep_entries import InvalidSleepEntry, SleepEntryDetails, validate_sleep_entry


class SleepEntryRuleTests(unittest.TestCase):
    def test_zero_maximum_and_prior_dates_are_explicit_values(self):
        today = date(2026, 11, 13)
        self.assertEqual(validate_sleep_entry(today, 0, today), SleepEntryDetails(today, 0))
        self.assertEqual(validate_sleep_entry(today - timedelta(days=1), 1440, today).sleep_minutes, 1440)
        entry = validate_sleep_entry(today, 450, today)
        with self.assertRaises(FrozenInstanceError):
            entry.sleep_minutes = 470

    def test_invalid_dates_and_coercible_durations_fail(self):
        today = date(2026, 11, 13)
        for day, minutes in ((today + timedelta(days=1), 450), ("2026-11-13", 450),
                             (datetime(2026, 11, 13), 450), (today, True), (today, 7.5),
                             (today, "450"), (today, -1), (today, 1441)):
            with self.subTest(day=day, minutes=minutes), self.assertRaises(InvalidSleepEntry):
                validate_sleep_entry(day, minutes, today)
        with self.assertRaises(InvalidSleepEntry):
            validate_sleep_entry(today, 450, "2026-11-13")
