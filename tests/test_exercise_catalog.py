"""Pinned source provenance, complete equipment, and malformed catalog rejection."""

from dataclasses import FrozenInstanceError
import json
import unittest
from unittest.mock import patch

from backend.catalogs import CATALOG_ROOT, decode_catalog, load_exercises
from backend.services.catalogs import InvalidCatalog, exercises_for_equipment, validate_exercise


class ExerciseCatalogTests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads((CATALOG_ROOT / "exercises.json").read_text())["records"]

    def test_six_records_match_the_pinned_source_and_preserve_classifications(self):
        exercises = load_exercises()
        self.assertEqual(len(exercises), 6)
        evidence = json.loads((CATALOG_ROOT / "sources" / "free-exercise-db.json").read_text())
        sources = {record["id"]: record for record in evidence["records"]}
        for exercise in exercises:
            upstream = sources[exercise.source_id]
            self.assertEqual(exercise.name, upstream["name"])
            self.assertEqual(exercise.source_level, upstream["level"])
            self.assertEqual(exercise.source_revision, evidence["source_revision"])
            self.assertEqual(set(exercise.primary_muscles), set(upstream["primaryMuscles"]))
        with self.assertRaises(FrozenInstanceError):
            exercises[0].name = "changed"

    def test_bench_and_bar_requirements_are_not_lost_by_single_equipment_labels(self):
        catalog = {exercise.source_id: exercise for exercise in load_exercises()}
        self.assertEqual(set(catalog["Dumbbell_Bench_Press"].required_equipment), {"bench", "dumbbells"})
        self.assertEqual(set(catalog["One-Arm_Dumbbell_Row"].required_equipment), {"bench", "dumbbells"})
        self.assertEqual(catalog["Pullups"].required_equipment, ("pull_up_bar",))
        available = exercises_for_equipment(tuple(catalog.values()), [])
        self.assertEqual({exercise.source_id for exercise in available}, {"Bodyweight_Squat", "Pushups", "Plank"})
        self.assertNotIn(catalog["Dumbbell_Bench_Press"], exercises_for_equipment(tuple(catalog.values()), ["dumbbells"]))
        self.assertIn(catalog["Dumbbell_Bench_Press"], exercises_for_equipment(tuple(catalog.values()), ["dumbbells", "bench"]))

    def test_missing_unknown_duplicate_and_unpinned_metadata_fail(self):
        original = self.records[0]
        cases = [original | {"source_revision":"main"}, original | {"source_url":"https://example.invalid"},
                 original | {"license":"unknown"}, original | {"required_equipment":["gym"]},
                 original | {"required_equipment":["bench", "bench"]}, original | {"required_equipment":None},
                 original | {"primary_muscles":[]}, original | {"name":True}, original | {"role":"admin"}]
        missing = dict(original)
        del missing["required_equipment"]
        for record in cases + [missing]:
            with self.subTest(record=record), self.assertRaises(InvalidCatalog):
                validate_exercise(record)
        for equipment in ["dumbbells", ["gym"], ["bench", "bench"]]:
            with self.assertRaises(InvalidCatalog):
                exercises_for_equipment(load_exercises(), equipment)

    def test_ambiguous_oversized_and_unknown_schema_json_fail(self):
        for raw in [b'{"schema_version":1,"schema_version":1,"records":[]}', b'{"schema_version":NaN,"records":[]}',
                    b'{"schema_version":true,"records":[]}', b'{"schema_version":2,"records":[]}',
                    b'\xff', b' ' * (256 * 1024 + 1), b'{"schema_version":1,"records":[]}']:
            with self.assertRaises(InvalidCatalog):
                decode_catalog(raw)
        with patch("backend.catalogs.decode_catalog", return_value=[self.records[0], self.records[0]]):
            with self.assertRaises(InvalidCatalog):
                load_exercises()
