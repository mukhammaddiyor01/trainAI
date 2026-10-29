"""Basic profile values and validation, without web or ORM dependencies."""

from dataclasses import dataclass
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class InvalidProfile(ValueError):
    """A basic profile is outside the application's supported input range."""


@dataclass(frozen=True)
class ProfileDetails:
    age: int
    height_cm: float
    weight_kg: float
    timezone: str


def validate_profile(age: int, height_cm: float, weight_kg: float, timezone: str) -> ProfileDetails:
    if type(age) is not int or not 18 <= age <= 120:
        raise InvalidProfile("Enter an age from 18 to 120. This version is for adults.")
    for value, minimum, maximum, message in [
        (height_cm, 50, 300, "Enter a height from 50 to 300 cm."),
        (weight_kg, 20, 500, "Enter a weight from 20 to 500 kg."),
    ]:
        if type(value) not in (int, float) or not minimum <= value <= maximum or not math.isfinite(value):
            raise InvalidProfile(message)
    if not isinstance(timezone, str) or not 1 <= len(timezone) <= 64:
        raise InvalidProfile("Choose a valid IANA time zone.")
    timezone = timezone.strip()
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise InvalidProfile("Choose a valid IANA time zone, such as Asia/Seoul.") from None
    return ProfileDetails(age, float(height_cm), float(weight_kg), timezone)
