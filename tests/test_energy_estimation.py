"""Independent adult EER fixtures, uncertainty/scope rejection, and current-profile inputs."""

from dataclasses import FrozenInstanceError, replace
from itertools import product
import os
import unittest
from unittest.mock import patch

from backend.services.energy_estimation import ENERGY_METHOD_VERSION, EnergyEstimateUnavailable, estimate_adult_energy
from backend.services.energy_preferences import (
    ENERGY_ACTIVITY_CATEGORIES, ENERGY_CONTEXTS, EQUATION_SEX_OPTIONS,
    validate_energy_preferences,
)
from backend.services.profiles import validate_profile


class EnergyEstimationTests(unittest.TestCase):
    def setUp(self):
        self.profile = validate_profile(30, 175, 70, "Asia/Seoul")
        self.preferences = validate_energy_preferences("male", "inactive", "general_adult")

    def test_all_eight_adult_equations_match_independent_table_5_16_fixtures(self):
        # Hand-evaluated for age 30 years, height 175 cm, weight 70 kg.
        expected = {
            ("male", "inactive"): 2552.67,
            ("male", "low_active"): 2754.87,
            ("male", "active"): 2934.62,
            ("male", "very_active"): 3226.67,
            ("female", "inactive"): 2195.30,
            ("female", "low_active"): 2370.27,
            ("female", "active"): 2508.25,
            ("female", "very_active"): 2767.98,
        }
        for (sex, activity), value in expected.items():
            with self.subTest(sex=sex, activity=activity):
                choices = validate_energy_preferences(sex, activity, "general_adult")
                result = estimate_adult_energy(self.profile, choices)
                self.assertAlmostEqual(result.energy_kcal_per_day, value)
                self.assertEqual(result.method_version, "dri-2023-adult-eer-v1")
                self.assertEqual((result.equation_sex, result.activity_category), (sex, activity))

    def test_fractional_profile_values_are_not_rounded_before_or_after_calculation(self):
        profile = validate_profile(67, 163.4, 62.3, "Asia/Seoul")
        choices = validate_energy_preferences("female", "active", "general_adult")
        result = estimate_adult_energy(profile, choices)
        self.assertAlmostEqual(result.energy_kcal_per_day, 2077.998)
        self.assertNotEqual(result.energy_kcal_per_day, round(result.energy_kcal_per_day))

    def test_every_uncertain_or_excluded_context_blocks_instead_of_defaulting(self):
        for sex, activity, context in product(EQUATION_SEX_OPTIONS, ENERGY_ACTIVITY_CATEGORIES, ENERGY_CONTEXTS):
            if sex != "unsure" and activity != "unsure" and context == "general_adult":
                continue
            with self.subTest(sex=sex, activity=activity, context=context):
                choices = validate_energy_preferences(sex, activity, context)
                with self.assertRaises(EnergyEstimateUnavailable):
                    estimate_adult_energy(self.profile, choices)

    def test_age_18_remains_a_valid_profile_but_does_not_use_an_adult_equation(self):
        adult_onboarding = validate_profile(18, 175, 70, "Asia/Seoul")
        with self.assertRaises(EnergyEstimateUnavailable):
            estimate_adult_energy(adult_onboarding, self.preferences)
        self.assertAlmostEqual(estimate_adult_energy(replace(adult_onboarding, age=19),
                                                    self.preferences).energy_kcal_per_day, 2671.80)

    def test_missing_and_manually_constructed_invalid_service_values_are_revalidated(self):
        for invalid in [None, {}, self.preferences]:
            with self.assertRaises(EnergyEstimateUnavailable):
                estimate_adult_energy(invalid, self.preferences)
        for invalid in [None, {}, self.profile]:
            with self.assertRaises(EnergyEstimateUnavailable):
                estimate_adult_energy(self.profile, invalid)
        for change in [dict(age=True), dict(age=121), dict(height_cm="175"), dict(weight_kg=-1),
                       dict(height_cm=float("inf")), dict(weight_kg=float("nan")),
                       dict(weight_kg=10 ** 1000), dict(timezone="private-input-marker")]:
            with self.assertRaises(ValueError) as caught:
                estimate_adult_energy(replace(self.profile, **change), self.preferences)
            self.assertNotIn("private-input-marker", str(caught.exception))
        for change in [dict(equation_sex=[]), dict(activity_category="mostly_seated"), dict(context=None)]:
            with self.assertRaises(ValueError):
                estimate_adult_energy(self.profile, replace(self.preferences, **change))

    def test_current_profile_weight_is_used_and_time_zone_does_not_change_energy(self):
        result = estimate_adult_energy(self.profile, self.preferences)
        changed_weight = estimate_adult_energy(replace(self.profile, weight_kg=80), self.preferences)
        self.assertAlmostEqual(changed_weight.energy_kcal_per_day - result.energy_kcal_per_day, 141)
        changed_zone = estimate_adult_energy(replace(self.profile, timezone="America/New_York"), self.preferences)
        self.assertEqual(changed_zone, result)

    def test_nonpositive_equation_result_is_rejected_without_clamping_to_a_target(self):
        # Supported onboarding bounds do not imply a clinically suitable calculation.
        profile = validate_profile(120, 50, 20, "Asia/Seoul")
        choices = validate_energy_preferences("male", "very_active", "general_adult")
        with self.assertRaises(EnergyEstimateUnavailable):
            estimate_adult_energy(profile, choices)

    def test_estimate_is_immutable_and_runs_without_database_or_network(self):
        with patch.dict(os.environ, {"DATABASE_URL": "must-not-be-read"}), \
                patch("socket.socket", side_effect=AssertionError("Network access is not allowed")):
            result = estimate_adult_energy(self.profile, self.preferences)
        self.assertEqual(result.method_version, ENERGY_METHOD_VERSION)
        with self.assertRaises(FrozenInstanceError):
            result.energy_kcal_per_day = 0
