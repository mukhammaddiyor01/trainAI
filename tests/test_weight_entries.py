"""Dated weight values stay strict and independent of server time."""

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta
import unittest

from backend.services.weight_entries import InvalidWeightEntry, validate_weight_entry


class WeightEntryRuleTests(unittest.TestCase):
    def test_today_and_historical_dates_are_explicit_immutable_observations(self):
        today = date(2026, 11, 11)
        current = validate_weight_entry(today, 70, today)
        older = validate_weight_entry(today - timedelta(days=4), 69.75, today)
        self.assertEqual((current.local_date, current.weight_kg), (today, 70.0))
        self.assertEqual(older.weight_kg, 69.75)
        with self.assertRaises(FrozenInstanceError):
            current.weight_kg = 90

    def test_future_dates_and_invalid_date_types_fail(self):
        today = date(2026, 11, 11)
        for local_date in (today + timedelta(days=1), "2026-11-11", datetime(2026, 11, 11), None):
            with self.subTest(local_date=local_date), self.assertRaises(InvalidWeightEntry):
                validate_weight_entry(local_date, 70, today)
        for invalid_today in (None, "2026-11-11", datetime(2026, 11, 11)):
            with self.subTest(today=invalid_today), self.assertRaises(InvalidWeightEntry):
                validate_weight_entry(today, 70, invalid_today)

    def test_weight_bounds_reject_coercion_and_nonfinite_values(self):
        today = date(2026, 11, 11)
        for value in (19.99, 500.01, True, "70", None, float("nan"), float("inf"), -float("inf")):
            with self.subTest(weight=value), self.assertRaises(InvalidWeightEntry):
                validate_weight_entry(today, value, today)
        self.assertEqual(validate_weight_entry(today, 20, today).weight_kg, 20.0)
        self.assertEqual(validate_weight_entry(today, 500, today).weight_kg, 500.0)
