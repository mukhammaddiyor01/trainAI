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
