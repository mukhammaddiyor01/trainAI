"""Owner-scoped persistence for explicit movement limitation self-reports."""

from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from backend.database import session_scope
from backend.models import MovementLimitations
from backend.services.movement_limitations import MovementLimitationsDetails, validate_movement_limitations


def read_movement_limitations(user_id: UUID) -> MovementLimitationsDetails | None:
    with session_scope() as session:
        row = session.get(MovementLimitations, user_id)
        return None if row is None else validate_movement_limitations(row.status)


def save_movement_limitations(user_id: UUID, details: MovementLimitationsDetails) -> MovementLimitationsDetails:
    details = validate_movement_limitations(details.status)
    statement = insert(MovementLimitations).values(user_id=user_id, status=details.status)
    statement = statement.on_conflict_do_update(
        index_elements=[MovementLimitations.user_id], set_={"status": details.status},
    )
    with session_scope() as session:
        session.execute(statement)
    return details
