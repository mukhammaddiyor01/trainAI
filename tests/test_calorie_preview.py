"""Requested calorie previews preserve scope, snapshots, precision, and explicit intent."""

from dataclasses import FrozenInstanceError, replace
import os
import unittest
from unittest.mock import patch

from backend.services.calorie_preview import (
    CaloriePreviewUnavailable, InvalidCalorieAdjustment, preview_calorie_adjustment,
)
from backend.services.energy_preferences import validate_energy_preferences
from backend.services.goals import GoalDetails, validate_goal
from backend.services.profiles import validate_profile


class CaloriePreviewTests(unittest.TestCase):
    def setUp(self):
        self.profile = validate_profile(30, 175, 70, "Asia/Seoul")
        self.choices = validate_energy_preferences("male", "inactive", "general_adult")

    def preview(self, direction, target, adjustment, profile=None, choices=None):
        return preview_calorie_adjustment(profile or self.profile, choices or self.choices,
                                           validate_goal(direction, 70, target), adjustment)

    def test_gain_loss_and_maintenance_use_explicit_amount_and_goal_direction(self):
        gain = self.preview("gain", 75, 200)
        loss = self.preview("lose", 65, 200)
        maintain = self.preview("maintain", None, 0)
        for value in (gain, loss, maintain):
            self.assertAlmostEqual(value.maintenance_kcal_per_day, 2552.67)
            self.assertEqual(value.energy_method_version, "dri-2023-adult-eer-v1")
            self.assertEqual(value.policy_version, "manual-adjustment-preview-2026-11-04-v1")
            self.assertEqual(value.status, "preview")
        self.assertEqual((gain.adjustment_kcal_per_day, loss.adjustment_kcal_per_day, maintain.adjustment_kcal_per_day),
                         (200, -200, 0))
        self.assertAlmostEqual(gain.preview_kcal_per_day, 2752.67)
        self.assertAlmostEqual(loss.preview_kcal_per_day, 2352.67)
        self.assertEqual(maintain.preview_kcal_per_day, maintain.maintenance_kcal_per_day)
        self.assertEqual((gain.goal_direction, loss.goal_direction, maintain.goal_direction), ("gain", "lose", "maintain"))

    def test_invalid_magnitudes_never_default_clamp_or_coerce(self):
        for amount in [None, True, False, "100", 100.0, 1.5, -1, 251, 10 ** 1000, float("nan"), float("inf"), [], {}]:
            with self.subTest(kind=type(amount).__name__), self.assertRaises(InvalidCalorieAdjustment):
                self.preview("gain", 75, amount)
        for direction, target, amount in [("maintain", None, 1), ("gain", 75, 0), ("lose", 65, 0)]:
            with self.assertRaises(InvalidCalorieAdjustment):
                self.preview(direction, target, amount)
        self.assertEqual(self.preview("gain", 75, 250).adjustment_kcal_per_day, 250)

    def test_relative_cap_rejects_above_ten_percent_without_changing_request(self):
        female = replace(self.choices, equation_sex="female")
        accepted = self.preview("lose", 65, 219, choices=female)
        self.assertAlmostEqual(accepted.maintenance_kcal_per_day, 2195.30)
        self.assertEqual(accepted.adjustment_kcal_per_day, -219)
        with self.assertRaises(InvalidCalorieAdjustment):
            self.preview("lose", 65, 220, choices=female)

    def test_floor_applies_to_result_and_does_not_raise_or_clamp_a_low_preview(self):
        profile = validate_profile(70, 150, 50, "UTC")
        choices = replace(self.choices, equation_sex="female")
        goal = validate_goal("lose", 50, 49)
        accepted = preview_calorie_adjustment(profile, choices, goal, 37)
        self.assertAlmostEqual(accepted.maintenance_kcal_per_day, 1537.70)
        self.assertAlmostEqual(accepted.preview_kcal_per_day, 1500.70)
        with self.assertRaises(CaloriePreviewUnavailable):
            preview_calorie_adjustment(profile, choices, goal, 38)
        low = replace(profile, weight_kg=45)
        with self.assertRaises(CaloriePreviewUnavailable):
            preview_calorie_adjustment(low, choices, validate_goal("maintain", 45, None), 0)

    def test_bmi_scope_checks_current_and_target_without_rounding_into_range(self):
        for current in [56.65, 122.5]:  # Below BMI 18.5 and exactly BMI 40 at 175 cm.
            with self.assertRaises(CaloriePreviewUnavailable):
                self.preview("maintain", None, 0, profile=replace(self.profile, weight_kg=current))
        for direction, target in [("lose", 56.65), ("gain", 122.5)]:
            with self.assertRaises(CaloriePreviewUnavailable):
                self.preview(direction, target, 100)
        self.assertEqual(self.preview("lose", 56.65625, 100).status, "preview")  # Exact BMI 18.5.
        self.assertEqual(self.preview("gain", 122.49, 100).status, "preview")

    def test_current_weight_updates_energy_but_do_not_rewrite_goal_baseline_or_infer_completion(self):
        goal = validate_goal("gain", 70, 75)
        changed = replace(self.profile, weight_kg=72)
        result = preview_calorie_adjustment(changed, self.choices, goal, 100)
        self.assertAlmostEqual(result.maintenance_kcal_per_day, 2580.87)
        self.assertEqual(goal.starting_weight_kg, 70)
        for current in [75, 76]:
            with self.assertRaises(CaloriePreviewUnavailable):
                preview_calorie_adjustment(replace(changed, weight_kg=current), self.choices, goal, 100)
        loss = validate_goal("lose", 70, 65)
        for current in [65, 64]:
            with self.assertRaises(CaloriePreviewUnavailable):
                preview_calorie_adjustment(replace(changed, weight_kg=current), self.choices, loss, 100)
        maintenance = preview_calorie_adjustment(changed, self.choices, validate_goal("maintain", 70, None), 0)
        self.assertAlmostEqual(maintenance.preview_kcal_per_day, 2580.87)

    def test_missing_forged_and_energy_ineligible_inputs_cannot_bypass_validation(self):
        goal = validate_goal("gain", 70, 75)
        for invalid in [None, {}, self.choices]:
            with self.assertRaises(ValueError):
                preview_calorie_adjustment(self.profile, self.choices, invalid, 100)
        for bad in [GoalDetails("gain", 70, 65), GoalDetails("maintain", 70, 75), GoalDetails("private-marker", 70, 75)]:
            with self.assertRaises(ValueError) as caught:
                preview_calorie_adjustment(self.profile, self.choices, bad, 100)
            self.assertNotIn("private-marker", str(caught.exception))
        for choices in [replace(self.choices, equation_sex="unsure"), replace(self.choices, activity_category="unsure"),
                        *[replace(self.choices, context=context) for context in ("unsure", "pregnant", "breastfeeding", "clinical")]]:
            with self.assertRaises(ValueError):
                preview_calorie_adjustment(self.profile, choices, goal, 100)
        for profile in [None, replace(self.profile, age=18), replace(self.profile, weight_kg=True),
                        replace(self.profile, height_cm=float("inf")), replace(self.profile, weight_kg=float("nan"))]:
            with self.assertRaises(ValueError):
                preview_calorie_adjustment(profile, self.choices, goal, 100)

    def test_immutable_offline_preview_preserves_fractional_energy_without_side_effects(self):
        goal = validate_goal("gain", 70, 75)
        with patch.dict(os.environ, {"DATABASE_URL":"must-not-be-read"}), \
                patch("socket.socket", side_effect=AssertionError("Network access is not allowed")):
            result = preview_calorie_adjustment(self.profile, self.choices, goal, 111)
        self.assertAlmostEqual(result.preview_kcal_per_day, 2663.67)
        self.assertNotEqual(result.preview_kcal_per_day, round(result.preview_kcal_per_day))
        with self.assertRaises(FrozenInstanceError):
            result.status = "active"
        self.assertEqual(self.profile.weight_kg, 70)
        self.assertEqual(goal, validate_goal("gain", 70, 75))
