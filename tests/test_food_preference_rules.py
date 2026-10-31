"""Reported food preferences remain separate from food safety and plan generation."""

from dataclasses import FrozenInstanceError
import unittest

from backend.services.food_preferences import InvalidFoodPreferences, validate_food_preferences


class FoodPreferenceRuleTests(unittest.TestCase):
    def validate(self, **changes):
        values = dict(diet="mixed", allergy_status="unsure", allergies=[], budget_level="economical",
                      prep_minutes=20, meal_times=["08:00", "19:30"])
        return validate_food_preferences(**(values | changes))

    def test_unknown_and_none_reported_are_distinct_explicit_states(self):
        self.assertEqual(self.validate().allergy_status, "unsure")
        self.assertEqual(self.validate(allergy_status="none_reported").allergy_status, "none_reported")
        for change in [dict(allergy_status="listed"), dict(allergy_status=None),
                       dict(allergies=["milk"]), dict(allergy_status="none_reported", allergies=["milk"])]:
            with self.subTest(change=change), self.assertRaises(InvalidFoodPreferences):
                self.validate(**change)

    def test_allergy_names_are_canonical_bounded_and_detached(self):
        names, times = ["  Milk  ", "Sesame"], ["23:59", "00:00"]
        details = self.validate(allergy_status="listed", allergies=names, meal_times=times)
        names.clear()
        times.clear()
        self.assertEqual(details.allergies, ("milk", "sesame"))
        self.assertEqual(details.meal_times, ("00:00", "23:59"))
        with self.assertRaises(FrozenInstanceError):
            details.diet = "vegan"
        for names in [["milk", " MILK "], [" "], ["a" * 65], ["milk\n"], ["\u202e"], [None], [["milk"]], ["x"] * 21, "milk"]:
            with self.subTest(names=names), self.assertRaises(InvalidFoodPreferences):
                self.validate(allergy_status="listed", allergies=names)

    def test_times_are_unique_strict_local_clock_values(self):
        for times in [[], ["8:00"], ["24:00"], ["12:60"], ["08:00:00"], ["08:00 "],
                      ["08:00", "08:00"], ["08:00"] * 9, [800], [True], [["08:00"]], "08:00"]:
            with self.subTest(times=times), self.assertRaises(InvalidFoodPreferences):
                self.validate(meal_times=times)

    def test_budget_is_explicit_spending_style_not_an_invented_price(self):
        for diet in ("mixed", "vegetarian", "vegan"):
            for budget in ("economical", "standard", "flexible"):
                self.assertEqual(self.validate(diet=diet, budget_level=budget).budget_level, budget)
        for changes in [dict(diet="keto"), dict(diet=[]), dict(budget_level=100), dict(budget_level="cheap")]:
            with self.assertRaises(InvalidFoodPreferences):
                self.validate(**changes)

    def test_zero_preparation_is_allowed_and_duration_is_not_coerced(self):
        self.assertEqual(self.validate(prep_minutes=0).prep_minutes, 0)
        self.assertEqual(self.validate(prep_minutes=180).prep_minutes, 180)
        for value in [True, "20", 20.0, -1, 181, None, float("nan"), 10 ** 1000]:
            with self.subTest(kind=type(value).__name__), self.assertRaises(InvalidFoodPreferences):
                self.validate(prep_minutes=value)
