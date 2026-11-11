"""Plain validation for explicitly dated weight observations."""

from dataclasses import dataclass
from datetime import date
import math


MIN_WEIGHT_KG = 20
MAX_WEIGHT_KG = 500


class InvalidWeightEntry(ValueError):
    """An observation cannot be represented by the supported input contract."""


@dataclass(frozen=True)
class WeightEntryDetails:
    local_date: date
    weight_kg: float


def validate_weight_entry(local_date: date, weight_kg: float, today: date) -> WeightEntryDetails:
    """Validate a dated measurement against an explicit owner-local today."""
    if type(today) is not date or type(local_date) is not date:
        raise InvalidWeightEntry("Enter a valid local calendar date.")
    if local_date > today:
        raise InvalidWeightEntry("A weight entry cannot have a future local date.")
    if type(weight_kg) not in (int, float) or not math.isfinite(weight_kg) or not MIN_WEIGHT_KG <= weight_kg <= MAX_WEIGHT_KG:
        raise InvalidWeightEntry("Enter a weight from 20 to 500 kg.")
    return WeightEntryDetails(local_date, float(weight_kg))
