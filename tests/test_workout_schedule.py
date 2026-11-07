"""Recovery spacing and availability remain distinct from a prescribed plan."""

from dataclasses import replace
import unittest

from backend.services.training_preferences import (
    InvalidTrainingPreferences,
    validate_training_preferences,
)
from backend.services.workout_schedule import strength_day_pairs


class StrengthDayPairTests(unittest.TestCase):
    def preferences(self, weekdays):
        return validate_training_preferences(
            "beginner", "mostly_seated", [], weekdays, 30,
        )

    def test_available_pairs_are_sorted_without_selecting_a_schedule(self):
        self.assertEqual(
            strength_day_pairs(self.preferences([7, 5, 3, 1])),
            ((1, 3), (1, 5), (3, 5), (3, 7), (5, 7)),
        )
        self.assertEqual(len(strength_day_pairs(self.preferences(list(range(1, 8))))), 14)

    def test_adjacent_and_week_boundary_days_do_not_silently_become_pairs(self):
        for days in ([1], [1, 2], [7, 1], [2, 3]):
            with self.subTest(days=days):
                self.assertEqual(strength_day_pairs(self.preferences(days)), ())
        self.assertEqual(strength_day_pairs(self.preferences([1, 3])), ((1, 3),))
        self.assertEqual(strength_day_pairs(self.preferences([2, 3, 4])), ((2, 4),))

    def test_forged_or_missing_preferences_fail(self):
        for value in (None, {}, self.preferences([1, 3]).weekdays):
            with self.subTest(value=value), self.assertRaises(ValueError):
                strength_day_pairs(value)
        with self.assertRaises(InvalidTrainingPreferences):
            strength_day_pairs(replace(self.preferences([1, 3]), weekdays=(1, 1)))
