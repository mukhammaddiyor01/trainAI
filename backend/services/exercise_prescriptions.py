"""Exact-source review gaps for exercises, without authored prescriptions."""

from backend.services.catalogs import ExerciseDetails


SOURCE_REVISION = "f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5"

# These identities were inspected against the retained source records. The extra
# gaps describe failed evidence transfer, not a judgment that a movement is unsafe.
REVIEWED_IDENTITIES = {
    "exercise-bodyweight-squat": ("Bodyweight_Squat", (), ("chair_squat_variant_mismatch",)),
    "exercise-pushups": ("Pushups", (), ("wall_and_hand_position_variant_mismatch",)),
    "exercise-plank": ("Plank", (), ("bounded_hold_missing",)),
    "exercise-dumbbell-bench-press": ("Dumbbell_Bench_Press", ("bench", "dumbbells"), ()),
    "exercise-one-arm-dumbbell-row": ("One-Arm_Dumbbell_Row", ("bench", "dumbbells"), ()),
    "exercise-pullups": ("Pullups", ("pull_up_bar",), ()),
}

MISSING_PRESCRIPTION_FIELDS = (
    "suitability_unreviewed",
    "dose_unreviewed",
    "rest_and_recovery_unreviewed",
    "alternative_unreviewed",
)


def exercise_prescription_gaps(exercise: ExerciseDetails) -> tuple[str, ...]:
    """Report exact-ID evidence gaps; never infer a dose from source metadata."""
    if type(exercise) is not ExerciseDetails:
        raise ValueError("Validated exercise details are required.")
    identity = REVIEWED_IDENTITIES.get(exercise.id)
    if identity is None or (exercise.source_id, exercise.required_equipment) != identity[:2] \
            or exercise.source_revision != SOURCE_REVISION:
        return ("catalog_identity_unreviewed", *MISSING_PRESCRIPTION_FIELDS)
    return (*identity[2], *MISSING_PRESCRIPTION_FIELDS)
