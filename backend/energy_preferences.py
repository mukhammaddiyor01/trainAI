"""Owner-scoped atomic energy preferences; no inferred defaults or saved calorie targets."""

from uuid import UUID
from sqlalchemy.dialects.postgresql import insert

from backend.database import session_scope
from backend.models import EnergyPreferences
from backend.services.energy_preferences import EnergyPreferencesDetails, validate_energy_preferences


def read_energy_preferences(user_id: UUID) -> EnergyPreferencesDetails | None:
    with session_scope() as session:
        record = session.get(EnergyPreferences, user_id)
        if record is None:
            return None
        return validate_energy_preferences(record.equation_sex, record.activity_category, record.context)


def save_energy_preferences(user_id: UUID, details: EnergyPreferencesDetails) -> EnergyPreferencesDetails:
    details = validate_energy_preferences(details.equation_sex, details.activity_category, details.context)
    values = dict(equation_sex=details.equation_sex, activity_category=details.activity_category, context=details.context)
    statement = insert(EnergyPreferences).values(user_id=user_id, **values).on_conflict_do_update(
        index_elements=[EnergyPreferences.user_id], set_=values,
    )
    with session_scope() as session:
        session.execute(statement)
    return details
