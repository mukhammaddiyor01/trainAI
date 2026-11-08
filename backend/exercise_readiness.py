"""Owner-scoped, read-only snapshot for the exercise readiness view."""

from uuid import UUID

from sqlalchemy import select

from backend.database import session_scope
from backend.models import MovementLimitations, Profile, TrainingPreferences
from backend.services.movement_limitations import MovementLimitationsDetails, validate_movement_limitations
from backend.services.training_preferences import TrainingPreferencesDetails, validate_training_preferences
from backend.training_preferences import EQUIPMENT_BITS


def read_exercise_readiness_inputs(
    user_id: UUID,
) -> tuple[TrainingPreferencesDetails | None, MovementLimitationsDetails | None] | None:
    """Return current owner inputs in one SQL snapshot, or None without a profile."""
    with session_scope() as session:
        row = session.execute(
            select(TrainingPreferences, MovementLimitations)
            .select_from(Profile)
            .outerjoin(TrainingPreferences, TrainingPreferences.user_id == Profile.user_id)
            .outerjoin(MovementLimitations, MovementLimitations.user_id == Profile.user_id)
            .where(Profile.user_id == user_id)
        ).one_or_none()
        if row is None:
            return None
        training, movement = row
        preferences = None
        if training is not None:
            equipment = [name for bit, name in enumerate(EQUIPMENT_BITS)
                         if training.equipment_mask & (1 << bit)]
            weekdays = [day for day in range(1, 8)
                        if training.weekday_mask & (1 << (day - 1))]
            preferences = validate_training_preferences(
                training.experience, training.activity, equipment, weekdays, training.session_minutes,
            )
        limitations = None if movement is None else validate_movement_limitations(movement.status)
        return preferences, limitations
