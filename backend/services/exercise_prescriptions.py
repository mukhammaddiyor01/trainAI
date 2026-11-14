"""Exact-source review gaps for exercises, without authored prescriptions."""

from dataclasses import dataclass

from backend.services.catalogs import ExerciseDetails


SOURCE_REVISION = "f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5"

# These identities were inspected against the retained source records. The extra
# gaps describe failed evidence transfer, not a judgment that a movement is unsafe.
REVIEWED_IDENTITIES = {
    "exercise-bodyweight-squat": ("Bodyweight_Squat", "Bodyweight Squat", "push", ("quadriceps",), (),
                                  ("chair_squat_variant_mismatch",)),
    "exercise-pushups": ("Pushups", "Pushups", "push", ("chest",), (),
                         ("wall_and_hand_position_variant_mismatch",)),
    "exercise-plank": ("Plank", "Plank", "static", ("abdominals",), (), ()),
    "exercise-dumbbell-bench-press": ("Dumbbell_Bench_Press", "Dumbbell Bench Press", "push", ("chest",),
                                      ("bench", "dumbbells"), ()),
    "exercise-one-arm-dumbbell-row": ("One-Arm_Dumbbell_Row", "One-Arm Dumbbell Row", "pull", ("middle back",),
                                     ("bench", "dumbbells"), ()),
    "exercise-pullups": ("Pullups", "Pullups", "pull", ("lats",), ("pull_up_bar",), ()),
}

MISSING_PRESCRIPTION_FIELDS = (
    "suitability_unreviewed",
    "dose_unreviewed",
    "rest_and_recovery_unreviewed",
    "alternative_unreviewed",
)


@dataclass(frozen=True)
class ReviewedExerciseDose:
    exercise_id: str
    sets: int
    hold_seconds: int
    rest_seconds: int
    recovery: str


# ACE's linked Front Plank library and Kick Start warm-up support this bounded
# example. It is not a personal prescription or permission to select the ID.
FRONT_PLANK_DOSE = ReviewedExerciseDose("exercise-plank", 2, 15, 30, "non_consecutive_days")


def reviewed_exercise_dose(exercise: ExerciseDetails) -> ReviewedExerciseDose | None:
    """Return a source-matched dose example, never a personal suitability verdict."""
    if type(exercise) is not ExerciseDetails:
        raise ValueError("Validated exercise details are required.")
    identity = REVIEWED_IDENTITIES.get(exercise.id)
    current_facts = (exercise.source_id, exercise.name, exercise.force,
                     exercise.primary_muscles, exercise.required_equipment)
    if identity is None or current_facts != identity[:5] or exercise.source_revision != SOURCE_REVISION:
        return None
    if exercise.id == FRONT_PLANK_DOSE.exercise_id:
        return FRONT_PLANK_DOSE
    return None


def exercise_prescription_gaps(exercise: ExerciseDetails) -> tuple[str, ...]:
    """Report exact-ID evidence gaps; never infer a dose from source metadata."""
    if type(exercise) is not ExerciseDetails:
        raise ValueError("Validated exercise details are required.")
    identity = REVIEWED_IDENTITIES.get(exercise.id)
    current_facts = (exercise.source_id, exercise.name, exercise.force,
                     exercise.primary_muscles, exercise.required_equipment)
    if identity is None or current_facts != identity[:5] or exercise.source_revision != SOURCE_REVISION:
        return ("catalog_identity_unreviewed", *MISSING_PRESCRIPTION_FIELDS)
    if reviewed_exercise_dose(exercise) is not None:
        return ("suitability_unreviewed", "alternative_unreviewed")
    return (*identity[5], *MISSING_PRESCRIPTION_FIELDS)
