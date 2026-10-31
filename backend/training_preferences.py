"""Owner-scoped storage for validated, self-reported training preferences."""

from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from backend.database import session_scope
from backend.models import TrainingPreferences
from backend.services.training_preferences import TrainingPreferencesDetails, validate_training_preferences

# Storage bit positions are permanent. Changing these requires a data migration.
EQUIPMENT_BITS = ("dumbbells", "barbell", "resistance_bands", "bench", "pull_up_bar", "cable_machine", "weight_machines")


def read_training_preferences(user_id: UUID) -> TrainingPreferencesDetails | None:
    with session_scope() as session:
        record = session.get(TrainingPreferences, user_id)
        if record is None:
            return None
        equipment = [name for bit, name in enumerate(EQUIPMENT_BITS) if record.equipment_mask & (1 << bit)]
        weekdays = [day for day in range(1, 8) if record.weekday_mask & (1 << (day - 1))]
        return validate_training_preferences(record.experience, record.activity, equipment,
                                              weekdays, record.session_minutes)


def save_training_preferences(user_id: UUID, details: TrainingPreferencesDetails) -> TrainingPreferencesDetails:
    details = validate_training_preferences(details.experience, details.activity, details.equipment,
                                             details.weekdays, details.session_minutes)
    values = dict(experience=details.experience, activity=details.activity,
                  equipment_mask=sum(1 << EQUIPMENT_BITS.index(name) for name in details.equipment),
                  weekday_mask=sum(1 << (day - 1) for day in details.weekdays),
                  session_minutes=details.session_minutes)
    statement = insert(TrainingPreferences).values(user_id=user_id, **values).on_conflict_do_update(
        index_elements=[TrainingPreferences.user_id], set_=values,
    )
    with session_scope() as session:
        session.execute(statement)
    return details
