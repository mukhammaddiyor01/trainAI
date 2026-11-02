"""Explicit portion totals preserve source identity, missing values, and bounded inputs."""

from dataclasses import FrozenInstanceError, replace
import os
import unittest
from unittest.mock import patch

from backend.catalogs import load_foods
from backend.services.catalog_use import (
    FoodSelectionUnavailable, UnknownCatalogItem, food_selection_blockers,
    nutrition_for_portions, require_food_selection_review,
)
from backend.services.food_preferences import validate_food_preferences


class PortionTotalTests(unittest.TestCase):
    def setUp(self):
        self.foods = load_foods()

    def test_multiple_food_totals_use_each_exact_edible_gram_basis(self):
        total = nutrition_for_portions(self.foods, [("food-fdc-173944", 150), ("food-fdc-168878", 200)])
        self.assertAlmostEqual(total.energy_kcal, 393.5)
        self.assertAlmostEqual(total.protein_g, 7.015)
        self.assertAlmostEqual(total.fat_g, 1.055)
        self.assertAlmostEqual(total.carbohydrate_g, 90.60)
        self.assertEqual([(p.food_id, p.preparation_state, p.grams) for p in total.portions],
                         [("food-fdc-173944", "raw", 150.0), ("food-fdc-168878", "cooked", 200.0)])
        self.assertNotEqual(total.energy_kcal,
                            total.protein_g * 4 + total.carbohydrate_g * 4 + total.fat_g * 9)

    def test_repeated_rows_are_additive_and_raw_and_cooked_rice_stay_distinct(self):
        total = nutrition_for_portions(self.foods, (("food-fdc-168877", 100),
                                                   ("food-fdc-168878", 100),
                                                   ("food-fdc-168878", 50)))
        self.assertEqual(total.energy_kcal, 560)
        self.assertEqual(len(total.portions), 3)
        self.assertEqual([p.preparation_state for p in total.portions], ["raw", "cooked", "cooked"])
        split = nutrition_for_portions(self.foods, [("food-fdc-173944", .1)] * 50)
        combined = nutrition_for_portions(self.foods, [("food-fdc-173944", 5)])
        self.assertAlmostEqual(split.energy_kcal, combined.energy_kcal)

    def test_unknown_nutrient_propagates_independently_without_discarding_known_rows(self):
        foods = (replace(self.foods[0], energy_kcal=None, protein_g=None), *self.foods[1:])
        total = nutrition_for_portions(foods, [(foods[0].id, 100), (foods[1].id, 100)])
        self.assertIsNone(total.energy_kcal)
        self.assertIsNone(total.protein_g)
        self.assertAlmostEqual(total.fat_g, .50)
        self.assertAlmostEqual(total.carbohydrate_g, 36.65)
        self.assertEqual(total.portions[1].energy_kcal, 52)
        zero_food = replace(self.foods[0], energy_kcal=0, protein_g=0, fat_g=0, carbohydrate_g=0)
        zero = nutrition_for_portions((zero_food,), [(zero_food.id, 1)])
        self.assertEqual((zero.energy_kcal, zero.protein_g, zero.fat_g, zero.carbohydrate_g), (0, 0, 0, 0))

    def test_empty_oversized_or_malformed_collections_are_rejected_not_zero_filled(self):
        for rows in [[], (), None, "banana", {}, iter([]), [("food-fdc-173944", 1)] * 51,
                     [None], [{}], ["food-fdc-173944"], [("food-fdc-173944",)],
                     [("food-fdc-173944", 100, "extra")],
                     [{"food_id": "food-fdc-173944", "grams": 100}]]:
            with self.subTest(kind=type(rows).__name__), self.assertRaises(ValueError):
                nutrition_for_portions(self.foods, rows)
        for grams in [0, -1, 10001, True, "100", None, float("nan"), float("inf"), 10 ** 1000]:
            with self.subTest(grams_type=type(grams).__name__), self.assertRaises(ValueError):
                nutrition_for_portions(self.foods, [("food-fdc-173944", grams)])

    def test_unknown_ids_fail_the_whole_calculation_without_skipping_bad_rows(self):
        for unknown in [None, True, [], 173944, "banana", "food-fdc-0"]:
            with self.subTest(kind=type(unknown).__name__), self.assertRaises(UnknownCatalogItem):
                nutrition_for_portions(self.foods, [("food-fdc-173944", 100), (unknown, 100)])

    def test_result_is_immutable_and_detached_from_input_rows(self):
        rows = [["food-fdc-173944", 100]]
        result = nutrition_for_portions(self.foods, rows)
        rows[0][1] = 200
        rows.clear()
        self.assertEqual(result.portions[0].grams, 100)
        self.assertEqual(result.energy_kcal, 89)
        with self.assertRaises(FrozenInstanceError):
            result.energy_kcal = 0
        with self.assertRaises(FrozenInstanceError):
            result.portions[0].grams = 0

    def test_totals_need_no_network_database_or_food_eligibility_approval(self):
        preferences = validate_food_preferences("vegan", "listed", ["milk"], "economical", 0, ["08:00"])
        before = food_selection_blockers(self.foods[0], preferences)
        with patch.dict(os.environ, {"DATABASE_URL": "must-not-be-read"}), \
                patch("socket.socket", side_effect=AssertionError("Network access is not allowed")):
            total = nutrition_for_portions(self.foods, [("food-fdc-173944", 100)])
        self.assertEqual(total.energy_kcal, 89)
        self.assertEqual(food_selection_blockers(self.foods[0], preferences), before)
        with self.assertRaises(FoodSelectionUnavailable):
            require_food_selection_review(self.foods[0], preferences)
