"""Plain validation for user-reported sleep duration on an explicit local date."""

from dataclasses import dataclass
from datetime import date


MAX_SLEEP_MINUTES = 1440


class InvalidSleepEntry(ValueError):
    """An entry violates the supported date or duration contract."""


@dataclass(frozen=True)
class SleepEntryDetails:
    local_date: date
    sleep_minutes: int


def validate_sleep_entry(local_date: date, sleep_minutes: int, today: date) -> SleepEntryDetails:
    """Keep zero distinct from missing and reject future owner-local dates."""
    if type(today) is not date or type(local_date) is not date or local_date > today:
        raise InvalidSleepEntry("Enter a valid local date that is not in the future.")
    if type(sleep_minutes) is not int or not 0 <= sleep_minutes <= MAX_SLEEP_MINUTES:
        raise InvalidSleepEntry("Enter a duration from 0 to 1440 minutes.")
    return SleepEntryDetails(local_date, sleep_minutes)
