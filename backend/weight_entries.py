"""Owner-scoped weight observations keyed by the user's local calendar date."""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from backend.database import session_scope
from backend.models import Profile, WeightEntry
from backend.services.profiles import validate_profile
from backend.services.weight_entries import InvalidWeightEntry, WeightEntryDetails, validate_weight_entry


MAX_RECENT_WEIGHT_ENTRIES = 30


class WeightProfileRequired(ValueError):
    """A profile with an explicit time zone is needed to date observations."""


def save_weight_entry(
    user_id: UUID, details: WeightEntryDetails, now_utc: datetime | None = None,
) -> WeightEntryDetails:
    """Create or explicitly correct one owner-local date without editing the profile."""
    if type(details) is not WeightEntryDetails:
        raise InvalidWeightEntry("A validated weight entry is required.")
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if type(now_utc) is not datetime or now_utc.utcoffset() != timedelta(0):
        raise ValueError("An aware UTC clock value is required.")
    with session_scope() as session:
        profile_row = session.scalar(select(Profile).where(Profile.user_id == user_id).with_for_update())
        if profile_row is None:
            raise WeightProfileRequired("Save a basic profile before recording weight.")
        profile = validate_profile(profile_row.age, profile_row.height_cm,
                                   profile_row.weight_kg, profile_row.timezone)
        today = now_utc.astimezone(ZoneInfo(profile.timezone)).date()
        entry = validate_weight_entry(details.local_date, details.weight_kg, today)
        statement = insert(WeightEntry).values(
            user_id=user_id, local_date=entry.local_date, weight_kg=entry.weight_kg,
        ).on_conflict_do_update(
            index_elements=[WeightEntry.user_id, WeightEntry.local_date],
            set_={"weight_kg": entry.weight_kg, "updated_at": func.now()},
        )
        session.execute(statement)
    return entry


def list_recent_weight_entries(user_id: UUID) -> tuple[WeightEntryDetails, ...]:
    """Return at most 30 owner observations, newest local date first."""
    with session_scope() as session:
        rows = session.scalars(select(WeightEntry).where(WeightEntry.user_id == user_id)
                               .order_by(WeightEntry.local_date.desc())
                               .limit(MAX_RECENT_WEIGHT_ENTRIES)).all()
        return tuple(WeightEntryDetails(row.local_date, row.weight_kg) for row in rows)
