"""Weekly observations preserve missing dates and avoid single-entry change."""

from datetime import date, timedelta
import unittest

from backend.services.weight_entries import WeightEntryDetails
from backend.services.weight_review import InvalidWeightReview, summarize_weight_weeks


class WeightReviewRuleTests(unittest.TestCase):
    def test_monday_weeks_and_observed_difference_only_with_two_dates(self):
        today = date(2026, 11, 11)  # Wednesday
        entries = (
            WeightEntryDetails(date(2026, 11, 11), 71.5),
            WeightEntryDetails(date(2026, 11, 9), 72),
            WeightEntryDetails(date(2026, 11, 2), 70),
            WeightEntryDetails(date(2026, 10, 13), 74),
        )
        weeks = summarize_weight_weeks(today, entries)
        self.assertEqual(len(weeks), 5)
        self.assertEqual((weeks[0].week_start, weeks[0].week_end),
                         (date(2026, 11, 9), date(2026, 11, 15)))
        self.assertEqual(weeks[0].observed_dates, 2)
        self.assertEqual(weeks[0].first.local_date, date(2026, 11, 9))
        self.assertEqual(weeks[0].last.local_date, date(2026, 11, 11))
        self.assertEqual(weeks[0].observed_change_kg, -0.5)
        self.assertEqual(weeks[1].observed_dates, 1)
        self.assertIsNone(weeks[1].observed_change_kg)
        self.assertEqual(weeks[2].observed_dates, 0)
        self.assertIsNone(weeks[2].first)
        self.assertIsNone(weeks[2].last)
        self.assertIsNone(weeks[2].observed_change_kg)
        self.assertEqual(weeks[4].observed_dates, 1)

    def test_sunday_and_year_boundary_remain_monday_based(self):
        weeks = summarize_weight_weeks(date(2027, 1, 3), (
            WeightEntryDetails(date(2026, 12, 28), 70),
            WeightEntryDetails(date(2027, 1, 3), 71),
        ))
        self.assertEqual((weeks[0].week_start, weeks[0].week_end),
                         (date(2026, 12, 28), date(2027, 1, 3)))
        self.assertEqual(weeks[0].observed_change_kg, 1)

    def test_invalid_future_duplicate_old_or_unbounded_inputs_fail(self):
        today = date(2026, 11, 11)
        valid = WeightEntryDetails(today, 70)
        invalid_sets = (
            [valid], (valid, valid), (WeightEntryDetails(today + timedelta(days=1), 70),),
            (WeightEntryDetails(today - timedelta(days=36), 70),),
            (WeightEntryDetails(today, float("nan")),), tuple(valid for _ in range(36)),
        )
        for entries in invalid_sets:
            with self.subTest(entries=entries), self.assertRaises(InvalidWeightReview):
                summarize_weight_weeks(today, entries)
        with self.assertRaises(InvalidWeightReview):
            summarize_weight_weeks("2026-11-11", ())
