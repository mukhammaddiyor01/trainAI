"""Explicit calculation choices preserve uncertainty without inventing defaults."""

from dataclasses import FrozenInstanceError
from itertools import product
import unittest

from backend.services.energy_preferences import (
    ENERGY_ACTIVITY_CATEGORIES, ENERGY_CONTEXTS, EQUATION_SEX_OPTIONS,
    InvalidEnergyPreferences, validate_energy_preferences,
)


class EnergyPreferenceRuleTests(unittest.TestCase):
    def test_supported_choices_round_trip_including_uncertain_and_excluded_contexts(self):
        for sex, activity, context in product(EQUATION_SEX_OPTIONS, ENERGY_ACTIVITY_CATEGORIES, ENERGY_CONTEXTS):
            with self.subTest(sex=sex, activity=activity, context=context):
                details = validate_energy_preferences(sex, activity, context)
                self.assertEqual((details.equation_sex, details.activity_category, details.context),
                                 (sex, activity, context))

    def test_missing_coercible_and_unbounded_values_fail_without_echoing_input(self):
        for position in range(3):
            for value in [None, True, False, 0, 1.5, [], {}, (), "", " private-input-marker ", "x" * 10000]:
                args = ["male", "inactive", "general_adult"]
                args[position] = value
                with self.subTest(position=position, kind=type(value).__name__):
                    with self.assertRaises(InvalidEnergyPreferences) as caught:
                        validate_energy_preferences(*args)
                    self.assertNotIn("private-input-marker", str(caught.exception))

    def test_aliases_case_and_other_training_activity_labels_are_not_inferred(self):
        for sex in ["Male", "female ", "m", "f", "other"]:
            with self.assertRaises(InvalidEnergyPreferences):
                validate_energy_preferences(sex, "inactive", "general_adult")
        for activity in ["mostly_seated", "lightly_active", "moderately_active", "active ", "1.53"]:
            with self.assertRaises(InvalidEnergyPreferences):
                validate_energy_preferences("male", activity, "general_adult")
        for context in ["healthy", "none", "GENERAL_ADULT", "general_adult "]:
            with self.assertRaises(InvalidEnergyPreferences):
                validate_energy_preferences("male", "inactive", context)

    def test_choices_are_immutable_and_no_uncertain_choice_is_replaced(self):
        details = validate_energy_preferences("unsure", "unsure", "unsure")
        with self.assertRaises(FrozenInstanceError):
            details.equation_sex = "male"
        self.assertEqual((details.equation_sex, details.activity_category, details.context),
                         ("unsure", "unsure", "unsure"))
