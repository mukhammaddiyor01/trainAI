"""Validate an explicit movement limitation self-report without medical inference."""

from dataclasses import dataclass

LIMITATION_STATUSES = ("unsure", "none_reported", "needs_adaptation")


class InvalidMovementLimitations(ValueError):
    """The self-report is missing or outside the supported choices."""


@dataclass(frozen=True)
class MovementLimitationsDetails:
    status: str


def validate_movement_limitations(status: str) -> MovementLimitationsDetails:
    if type(status) is not str or status not in LIMITATION_STATUSES:
        raise InvalidMovementLimitations("Choose whether movement limitations need consideration.")
    return MovementLimitationsDetails(status=status)
