"""Exercise metadata and self-report never become automatic prescriptions."""

from dataclasses import replace
import unittest

from backend.catalogs import load_exercises
from backend.services.catalog_use import (
    ExerciseSelectionUnavailable, UnknownCatalogItem,
    exercise_selection_blockers, require_exercise_selection_review,
)
from backend.services.movement_limitations import InvalidMovementLimitations, validate_movement_limitations
from backend.services.training_preferences import InvalidTrainingPreferences, validate_training_preferences
from backend.services.exercise_prescriptions import exercise_prescription_gaps, reviewed_exercise_dose


class ExerciseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exercises = load_exercises()

    def preferences(self, equipment=()):
        return validate_training_preferences("beginner", "mostly_seated", equipment, [1, 3], 30)

    def test_missing_inputs_remain_distinct_and_block_selection(self):
        blockers = exercise_selection_blockers(self.exercises, "exercise-pushups", None, None)
        self.assertEqual(blockers, (
            "training_preferences_missing", "movement_answer_missing", "exercise_prescription_unreviewed",
        ))
        with self.assertRaises(ExerciseSelectionUnavailable):
            require_exercise_selection_review(self.exercises, "exercise-pushups", None, None)

    def test_all_six_records_stay_blocked_even_with_none_reported(self):
        preferences = self.preferences(("dumbbells", "bench", "pull_up_bar"))
        answer = validate_movement_limitations("none_reported")
        for exercise in self.exercises:
            with self.subTest(exercise=exercise.id):
                self.assertEqual(exercise_selection_blockers(self.exercises, exercise.id, preferences, answer),
                                 ("exercise_prescription_unreviewed",))
                with self.assertRaises(ExerciseSelectionUnavailable):
                    require_exercise_selection_review(self.exercises, exercise.id, preferences, answer)

    def test_review_gaps_cover_every_exact_catalog_identity(self):
        expected_special = {
            "exercise-bodyweight-squat": "chair_squat_variant_mismatch",
            "exercise-pushups": "wall_and_hand_position_variant_mismatch",
        }
        self.assertEqual(len(self.exercises), 6)
        for exercise in self.exercises:
            with self.subTest(exercise=exercise.id):
                gaps = exercise_prescription_gaps(exercise)
                self.assertNotIn("catalog_identity_unreviewed", gaps)
                self.assertIn("suitability_unreviewed", gaps)
                self.assertIn("alternative_unreviewed", gaps)
                if exercise.id == "exercise-plank":
                    self.assertEqual(gaps, ("suitability_unreviewed", "alternative_unreviewed"))
                else:
                    self.assertIn("dose_unreviewed", gaps)
                    self.assertIn("rest_and_recovery_unreviewed", gaps)
                if exercise.id in expected_special:
                    self.assertIn(expected_special[exercise.id], gaps)

    def test_bounded_front_plank_dose_is_only_reviewed_example(self):
        plank = next(exercise for exercise in self.exercises if exercise.id == "exercise-plank")
        dose = reviewed_exercise_dose(plank)
        self.assertEqual((dose.sets, dose.hold_seconds, dose.rest_seconds, dose.recovery),
                         (2, 15, 30, "non_consecutive_days"))
        self.assertTrue(all(reviewed_exercise_dose(exercise) is None for exercise in self.exercises
                            if exercise.id != plank.id))
        self.assertIsNone(reviewed_exercise_dose(replace(plank, source_revision="0" * 40)))
        self.assertIsNone(reviewed_exercise_dose(replace(plank, name="Other Plank")))
        self.assertIn("exercise_prescription_unreviewed", exercise_selection_blockers(
            self.exercises, plank.id, self.preferences(),
            validate_movement_limitations("none_reported"),
        ))

    def test_changed_source_or_equipment_cannot_inherit_review(self):
        exercise = self.exercises[0]
        for altered in (
            replace(exercise, source_revision="0" * 40),
            replace(exercise, source_id="Other_Squat"),
            replace(exercise, required_equipment=("bench",)),
            replace(exercise, name="Different Squat"),
        ):
            with self.subTest(altered=altered):
                self.assertEqual(exercise_prescription_gaps(altered)[0], "catalog_identity_unreviewed")
        with self.assertRaises(ValueError):
            exercise_prescription_gaps(None)

    def test_equipment_must_be_complete_and_source_level_grants_nothing(self):
        answer = validate_movement_limitations("none_reported")
        for equipment in ((), ("dumbbells",), ("bench",)):
            with self.subTest(equipment=equipment):
                blockers = exercise_selection_blockers(
                    self.exercises, "exercise-dumbbell-bench-press", self.preferences(equipment), answer,
                )
                self.assertEqual(blockers, ("equipment_unavailable", "exercise_prescription_unreviewed"))

    def test_uncertainty_and_adaptation_are_not_cleared_by_equipment(self):
        for status, expected in (("unsure", "movement_answer_unsure"),
                                 ("needs_adaptation", "adaptation_review_required")):
            with self.subTest(status=status):
                blockers = exercise_selection_blockers(
                    self.exercises, "exercise-bodyweight-squat", self.preferences(),
                    validate_movement_limitations(status),
                )
                self.assertEqual(blockers, (expected, "exercise_prescription_unreviewed"))

    def test_unknown_ids_and_forged_values_fail_closed(self):
        for exercise_id in (None, "Pushups", "exercise-invented", True):
            with self.subTest(exercise_id=exercise_id), self.assertRaises(UnknownCatalogItem):
                exercise_selection_blockers(self.exercises, exercise_id, self.preferences(),
                                            validate_movement_limitations("none_reported"))
        with self.assertRaises(InvalidTrainingPreferences):
            exercise_selection_blockers(self.exercises, "exercise-pushups",
                                        replace(self.preferences(), weekdays=(1, 1)),
                                        validate_movement_limitations("none_reported"))
        with self.assertRaises(InvalidMovementLimitations):
            exercise_selection_blockers(self.exercises, "exercise-pushups", self.preferences(),
                                        replace(validate_movement_limitations("unsure"), status="clear"))
