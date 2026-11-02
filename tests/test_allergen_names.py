"""Exact reviewed terms, preserved unknowns, bounds, and immutable resolution."""

from dataclasses import FrozenInstanceError
import unittest
from unittest.mock import patch

from backend.services.allergens import (ALLERGEN_GROUPS, MAPPING_VERSION,
                                        reviewed_allergen_aliases, resolve_allergy_names)
from backend.services.food_preferences import InvalidFoodPreferences, validate_food_preferences


class AllergenNameTests(unittest.TestCase):
    def test_reviewed_subset_has_nine_groups_and_fifteen_unambiguous_terms(self):
        aliases = reviewed_allergen_aliases()
        self.assertEqual(len(aliases),15)
        self.assertEqual(set(aliases.values()), {"milk","egg","fish","crustacean_shellfish","tree_nuts","peanut","wheat","soy","sesame"})
        for group,names in ALLERGEN_GROUPS:
            self.assertEqual(resolve_allergy_names(list(names)).allergen_ids,(group,))
        with self.assertRaises(TypeError):
            aliases["nuts"] = "peanut"

    def test_resolution_uses_saved_normalization_and_merges_aliases_without_mutating_names(self):
        names = [" Milk ", "SOYA", "soybeans", "TREE   NUTS"]
        preferences = validate_food_preferences("mixed","listed",names,"economical",20,["08:00"])
        direct = resolve_allergy_names(names)
        self.assertEqual(direct,resolve_allergy_names(preferences.allergies))
        self.assertEqual(direct.allergen_ids,("milk","soy","tree_nuts"))
        self.assertEqual(direct.unresolved_names,())
        self.assertEqual(direct.mapping_version,MAPPING_VERSION)
        self.assertEqual(names[0]," Milk ")
        with self.assertRaises(FrozenInstanceError):
            direct.allergen_ids = ()

    def test_unknown_ambiguous_species_and_translated_names_remain_unresolved(self):
        names = ["nuts","shellfish","coconut","lactose","gluten","almond","shrimp","sut","banana","milk free","not milk","milk, eggs","milkk"]
        result = resolve_allergy_names(names)
        self.assertEqual(result.allergen_ids,())
        self.assertEqual(result.unresolved_names,tuple(sorted(names)))
        mixed = resolve_allergy_names(["milk","banana"])
        self.assertEqual(mixed.allergen_ids,("milk",))
        self.assertEqual(mixed.unresolved_names,("banana",))
        self.assertEqual(resolve_allergy_names([]).unresolved_names,())

    def test_malformed_and_oversized_names_fail_without_guessing(self):
        for names in [None, "milk", {}, iter(["milk"]), [True], [["milk"]], ["a"*65], ["\n"],
                      [" "], ["milk"," MILK "], ["milk"]*21, ["\u202e"]]:
            with self.subTest(names_type=type(names).__name__), self.assertRaises(InvalidFoodPreferences):
                resolve_allergy_names(names)

    def test_duplicate_group_or_alias_and_unnormalized_registry_fail(self):
        for groups in [(('milk',('milk',)),('egg',('milk',))),
                       (('milk',('milk',)),('milk',('eggs',))),
                       (('milk',('MILK',)),), (('milk',()),)]:
            with self.subTest(groups=groups), patch("backend.services.allergens.ALLERGEN_GROUPS",groups):
                with self.assertRaises(ValueError):
                    reviewed_allergen_aliases()
