"""Preference validation runs without HTTP, database, models, or network."""

from dataclasses import FrozenInstanceError
import unittest

from backend.services.training_preferences import InvalidTrainingPreferences, validate_training_preferences


class TrainingPreferenceRuleTests(unittest.TestCase):
    def validate(self, **changes):
        values = dict(experience="beginner", activity="mostly_seated", equipment=[],
                      weekdays=[1, 3, 5], session_minutes=30)
        return validate_training_preferences(**(values | changes))

    def test_bodyweight_and_minimum_availability_do_not_imply_a_prescription(self):
        details = self.validate(weekdays=[7], session_minutes=10)
        self.assertEqual(details.equipment, ())
        self.assertEqual(details.weekdays, (7,))
        self.assertEqual(details.session_minutes, 10)
        self.assertEqual(self.validate(weekdays=list(range(1, 8)), session_minutes=180).session_minutes, 180)

    def test_saved_values_are_canonical_and_detached_from_mutable_inputs(self):
        equipment, weekdays = ["resistance_bands", "dumbbells"], [7, 1]
        details = self.validate(equipment=equipment, weekdays=weekdays)
        equipment.clear()
        weekdays.clear()
        self.assertEqual(details.equipment, ("dumbbells", "resistance_bands"))
        self.assertEqual(details.weekdays, (1, 7))
        with self.assertRaises(FrozenInstanceError):
            details.session_minutes = 40

    def test_unknown_duplicate_and_malformed_choices_fail_cleanly(self):
        cases = [dict(experience="expert"), dict(experience=[]), dict(activity=None),
                 dict(activity="moderate"), dict(equipment="dumbbells"),
                 dict(equipment=["gym"]), dict(equipment=[["dumbbells"]]),
                 dict(equipment=["bench", "bench"]), dict(equipment=["bench"] * 8),
                 dict(weekdays=[]), dict(weekdays=[1, 1]), dict(weekdays=[0]),
                 dict(weekdays=[8]), dict(weekdays=[True]), dict(weekdays=["1"]),
                 dict(weekdays=[1.0]), dict(weekdays=[[1]]), dict(weekdays=iter([1])),
                 dict(weekdays=[1] * 8)]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(InvalidTrainingPreferences):
                self.validate(**changes)

    def test_duration_does_not_coerce_booleans_strings_or_non_finite_values(self):
        for value in [True, "30", 30.0, None, 9, 181, float("nan"), float("inf"), 10 ** 1000]:
            with self.subTest(kind=type(value).__name__), self.assertRaises(InvalidTrainingPreferences):
                self.validate(session_minutes=value)
