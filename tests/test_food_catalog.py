"""Exact USDA values, raw/cooked identity, source evidence, units, and unknowns."""

from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from backend.catalogs import CATALOG_ROOT, load_foods
from backend.services.catalogs import InvalidCatalog, validate_food


class FoodCatalogTests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads((CATALOG_ROOT / "foods.json").read_text())["records"]

    def test_four_foods_match_retained_usda_source_values_and_units(self):
        foods = load_foods()
        self.assertEqual(len(foods), 4)
        for food in foods:
            evidence = json.loads((CATALOG_ROOT / "sources" / "usda-sr-legacy" / f"{food.source_id}.json").read_bytes())
            self.assertEqual(food.name, evidence["description"])
            self.assertEqual(evidence["dataType"], "SR Legacy")
            nutrients = {item["nutrient"]["id"]: item for item in evidence["foodNutrients"]}
            for key, attribute, unit in [(1008,"energy_kcal","kcal"), (1003,"protein_g","g"), (1004,"fat_g","g"), (1005,"carbohydrate_g","g")]:
                self.assertEqual(getattr(food,attribute), nutrients[key]["amount"])
                self.assertEqual(nutrients[key]["nutrient"]["unitName"].lower(),unit)
        self.assertEqual(foods[0].energy_kcal, 89)
        self.assertEqual(foods[0].protein_g, 1.09)

    def test_raw_and_cooked_rice_are_different_records_not_interchangeable(self):
        foods = {food.source_id:food for food in load_foods()}
        self.assertEqual(foods[168877].preparation_state,"raw")
        self.assertEqual(foods[168878].preparation_state,"cooked")
        self.assertEqual(foods[168877].energy_kcal,365)
        self.assertEqual(foods[168878].energy_kcal,130)
        for food in foods.values():
            self.assertIsNone(food.ingredient_ids)
            self.assertIsNone(food.allergen_tags)
            self.assertIsNone(food.diet_tags)
            self.assertEqual(food.review_status,"nutrition_only")

    def test_missing_nutrition_remains_unknown_not_zero_or_macro_calculated(self):
        record = deepcopy(self.records[0])
        record["nutrients"] = [item for item in record["nutrients"] if item["id"] != 1008]
        self.assertIsNone(validate_food(record).energy_kcal)
        record["nutrients"][0]["amount"] = None
        self.assertIsNone(validate_food(record).protein_g)

    def test_bad_units_duplicates_coercion_and_unsupported_metadata_fail(self):
        original = self.records[0]
        changes = [dict(basis_g=1),dict(basis_g=True),dict(source_id=True),dict(license="unknown"),
                   dict(source_release="latest"),dict(source_sha256="missing"),dict(retrieved_on="2026-02-30"),
                   dict(source_url="https://example.invalid"),dict(preparation_state="unknown"),
                   dict(allergen_tags=[]),dict(review_status="safe"),dict(user_id="forged")]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(InvalidCatalog):
                validate_food(original | change)
        for amount in [True,"89",-1,float("nan"),float("inf"),10 ** 1000]:
            record = deepcopy(original)
            record["nutrients"][0]["amount"] = amount
            with self.assertRaises(InvalidCatalog):
                validate_food(record)
        for key,value in [("unit","kJ"),("id",True),("id",9999)]:
            record = deepcopy(original)
            record["nutrients"][0][key] = value
            with self.assertRaises(InvalidCatalog):
                validate_food(record)
        record = deepcopy(original)
        record["nutrients"] = [record["nutrients"][0]] * 2
        with self.assertRaises(InvalidCatalog):
            validate_food(record)

    def test_corrupted_source_snapshot_is_rejected(self):
        record = self.records[0] | dict(source_sha256="0" * 64)
        with patch("backend.catalogs.decode_catalog",return_value=[record]):
            with self.assertRaises(InvalidCatalog):
                load_foods()
