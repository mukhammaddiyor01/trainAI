"""Monday-based summaries of explicit weight observations, without advice."""

from dataclasses import dataclass
from datetime import date, timedelta

from backend.services.weight_entries import WeightEntryDetails, validate_weight_entry


REVIEW_WEEKS = 5


class InvalidWeightReview(ValueError):
    """Review inputs violate the bounded observation contract."""


@dataclass(frozen=True)
class WeeklyWeightSummary:
    week_start: date
    week_end: date
    observed_dates: int
    first: WeightEntryDetails | None
    last: WeightEntryDetails | None
    observed_change_kg: float | None


def summarize_weight_weeks(today: date, entries: tuple[WeightEntryDetails, ...]) -> tuple[WeeklyWeightSummary, ...]:
    """Summarize five local weeks; never fill missing dates or infer a trend."""
    if type(today) is not date or type(entries) is not tuple or len(entries) > REVIEW_WEEKS * 7:
        raise InvalidWeightReview("Enter a bounded local-date review.")
    current_monday = today - timedelta(days=today.weekday())
    oldest_monday = current_monday - timedelta(weeks=REVIEW_WEEKS - 1)
    observed: dict[date, WeightEntryDetails] = {}
    for candidate in entries:
        if type(candidate) is not WeightEntryDetails:
            raise InvalidWeightReview("Enter valid weight observations.")
        try:
            entry = validate_weight_entry(candidate.local_date, candidate.weight_kg, today)
        except ValueError:
            raise InvalidWeightReview("Enter valid weight observations.") from None
        if entry.local_date < oldest_monday or entry.local_date in observed:
            raise InvalidWeightReview("Enter unique dates inside the review window.")
        observed[entry.local_date] = entry

    result = []
    for offset in range(REVIEW_WEEKS):
        start = current_monday - timedelta(weeks=offset)
        end = start + timedelta(days=6)
        week = sorted((entry for day, entry in observed.items() if start <= day <= end),
                      key=lambda entry: entry.local_date)
        first, last = (week[0], week[-1]) if week else (None, None)
        change = last.weight_kg - first.weight_kg if len(week) >= 2 else None
        result.append(WeeklyWeightSummary(start, end, len(week), first, last, change))
    return tuple(result)
