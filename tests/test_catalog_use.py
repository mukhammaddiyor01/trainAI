"""Unknown IDs, gram units, raw/cooked identity, and conservative readiness checks."""

from dataclasses import replace
import unittest

from backend.catalogs import load_exercises, load_foods
from backend.services.catalog_use import (UnknownCatalogItem, FoodSelectionUnavailable, exercise_by_id,
                                         food_by_id, nutrition_for_grams, food_selection_blockers,
                                         require_food_selection_review)
from backend.services.food_preferences import validate_food_preferences


class CatalogUseTests(unittest.TestCase):
    def test_lookup_requires_known_ids_not_free_text_or_source_numbers(self):
        exercises, foods = load_exercises(), load_foods()
        self.assertEqual(exercise_by_id(exercises,"exercise-pushups").source_id,"Pushups")
        self.assertEqual(food_by_id(foods,"food-fdc-173944").source_id,173944)
        for unknown in [None, True, [], "banana", 173944, "food-fdc-0"]:
            with self.assertRaises(UnknownCatalogItem):
                food_by_id(foods,unknown)
        for unknown in [None, [], "Pushups", "exercise-unknown"]:
            with self.assertRaises(UnknownCatalogItem):
                exercise_by_id(exercises,unknown)

    def test_gram_scaling_preserves_known_source_values_and_preparation_identity(self):
        foods = load_foods()
        banana = food_by_id(foods,"food-fdc-173944")
        portion = nutrition_for_grams(banana,150)
        self.assertAlmostEqual(portion.energy_kcal,133.5)
        self.assertAlmostEqual(portion.protein_g,1.635)
        self.assertAlmostEqual(portion.carbohydrate_g,34.26)
        self.assertAlmostEqual(portion.fat_g,0.495)
        self.assertEqual(portion.food_id,banana.id)
        self.assertEqual(portion.grams,150)
        cooked = nutrition_for_grams(food_by_id(foods,"food-fdc-168878"),200)
        raw = nutrition_for_grams(food_by_id(foods,"food-fdc-168877"),200)
        self.assertEqual((cooked.energy_kcal,cooked.preparation_state),(260,"cooked"))
        self.assertEqual((raw.energy_kcal,raw.preparation_state),(730,"raw"))

    def test_missing_nutrients_stay_unknown_after_scaling(self):
        food = replace(load_foods()[0],energy_kcal=None,protein_g=None)
        portion = nutrition_for_grams(food,50)
        self.assertIsNone(portion.energy_kcal)
        self.assertIsNone(portion.protein_g)
        self.assertAlmostEqual(portion.fat_g,0.165)

    def test_invalid_portions_are_not_coerced(self):
        for grams in [0,-1,10001,True,"100",None,float("nan"),float("inf"),10 ** 1000]:
            with self.subTest(kind=type(grams).__name__), self.assertRaises(ValueError):
                nutrition_for_grams(load_foods()[0],grams)

    def test_no_seed_is_silently_eligible_for_food_selection(self):
        for status,allergies in [("unsure",[]),("none_reported",[]),("listed",["milk"]),("listed",["unmapped allergy"])]:
            preferences = validate_food_preferences("vegan",status,allergies,"economical",20,["08:00"])
            for food in load_foods():
                blockers = food_selection_blockers(food,preferences)
                self.assertIn("ingredients_unknown",blockers)
                self.assertIn("allergens_unknown",blockers)
                self.assertIn("diet_unknown",blockers)
                if status == "unsure":
                    self.assertIn("allergy_status_unsure",blockers)
                if status == "listed":
                    self.assertIn("allergy_mapping_unreviewed",blockers)
                with self.assertRaises(FoodSelectionUnavailable):
                    require_food_selection_review(food,preferences)

    def test_recognized_names_do_not_complete_ingredient_or_allergen_review(self):
        preferences = validate_food_preferences("vegan","listed",["soya","eggs"],"economical",20,["08:00"])
        for food in load_foods():
            blockers = food_selection_blockers(food,preferences)
            self.assertNotIn("allergy_names_unresolved",blockers)
            self.assertIn("allergy_mapping_unreviewed",blockers)
            self.assertIn("composition_unreviewed",blockers)
            self.assertIn("allergens_unknown",blockers)
            with self.assertRaises(FoodSelectionUnavailable):
                require_food_selection_review(food,preferences)

    def test_partial_or_ambiguous_name_resolution_cannot_drop_unknown_restrictions(self):
        for names in [["milk","banana"],["milk","nuts"],["milk free"],["shellfish"]]:
            preferences = validate_food_preferences("mixed","listed",names,"economical",0,["08:00"])
            for food in load_foods():
                blockers = food_selection_blockers(food,preferences)
                self.assertIn("allergy_names_unresolved",blockers)
                self.assertIn("allergy_mapping_unreviewed",blockers)
                with self.assertRaises(FoodSelectionUnavailable):
                    require_food_selection_review(food,preferences)
