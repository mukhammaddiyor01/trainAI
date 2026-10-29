"""Owner-scoped profile persistence; convert records into plain Python values."""

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from backend.database import session_scope
from backend.models import Profile
from backend.services.profiles import ProfileDetails


def read_profile(user_id: UUID) -> ProfileDetails | None:
    with session_scope() as session:
        profile = session.get(Profile, user_id)
        if profile is None:
            return None
        return ProfileDetails(profile.age, profile.height_cm, profile.weight_kg, profile.timezone)


def save_profile(user_id: UUID, details: ProfileDetails) -> ProfileDetails:
    values = {"age": details.age, "height_cm": details.height_cm,
              "weight_kg": details.weight_kg, "timezone": details.timezone}
    statement = insert(Profile).values(user_id=user_id, **values).on_conflict_do_update(
        index_elements=[Profile.user_id], set_={**values, "updated_at": func.now()},
    )
    with session_scope() as session:
        session.execute(statement)
    return details
