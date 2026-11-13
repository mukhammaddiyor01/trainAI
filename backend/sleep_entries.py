"""Owner-scoped sleep observations keyed by the user's local calendar date."""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from backend.database import session_scope
from backend.models import Profile, SleepEntry
from backend.services.profiles import validate_profile
from backend.services.sleep_entries import InvalidSleepEntry, SleepEntryDetails, validate_sleep_entry


MAX_RECENT_SLEEP_ENTRIES = 30


class SleepProfileRequired(ValueError):
    """A saved profile is needed to date an observation."""


def save_sleep_entry(user_id: UUID, details: SleepEntryDetails,
                     now_utc: datetime | None = None) -> SleepEntryDetails:
    """Create or correct one owner-local date without changing planning inputs."""
    if type(details) is not SleepEntryDetails:
        raise InvalidSleepEntry("A validated sleep entry is required.")
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if type(now_utc) is not datetime or now_utc.utcoffset() != timedelta(0):
        raise ValueError("An aware UTC clock value is required.")
    with session_scope() as session:
        profile_row = session.scalar(select(Profile).where(Profile.user_id == user_id).with_for_update())
        if profile_row is None:
            raise SleepProfileRequired("Save a basic profile before recording sleep.")
        profile = validate_profile(profile_row.age, profile_row.height_cm,
                                   profile_row.weight_kg, profile_row.timezone)
        today = now_utc.astimezone(ZoneInfo(profile.timezone)).date()
        entry = validate_sleep_entry(details.local_date, details.sleep_minutes, today)
        statement = insert(SleepEntry).values(
            user_id=user_id, local_date=entry.local_date, sleep_minutes=entry.sleep_minutes,
        ).on_conflict_do_update(
            index_elements=[SleepEntry.user_id, SleepEntry.local_date],
            set_={"sleep_minutes": entry.sleep_minutes, "updated_at": func.now()},
        )
        session.execute(statement)
    return entry


def list_recent_sleep_entries(user_id: UUID) -> tuple[SleepEntryDetails, ...]:
    """Return at most 30 owner observations, newest local date first."""
    with session_scope() as session:
        rows = session.scalars(select(SleepEntry).where(SleepEntry.user_id == user_id)
                               .order_by(SleepEntry.local_date.desc())
                               .limit(MAX_RECENT_SLEEP_ENTRIES)).all()
        return tuple(SleepEntryDetails(row.local_date, row.sleep_minutes) for row in rows)
