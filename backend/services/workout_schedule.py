"""Enumerate available nonconsecutive strength-day pairs without choosing a plan."""

from itertools import combinations

from backend.services.training_preferences import (
    TrainingPreferencesDetails,
    validate_training_preferences,
)


def strength_day_pairs(preferences: TrainingPreferencesDetails) -> tuple[tuple[int, int], ...]:
    """Return two-day options with a rest day between sessions in a repeating week."""
    if type(preferences) is not TrainingPreferencesDetails:
        raise ValueError("Validated training preferences are required.")
    preferences = validate_training_preferences(
        preferences.experience,
        preferences.activity,
        preferences.equipment,
        preferences.weekdays,
        preferences.session_minutes,
    )
    return tuple(
        (first, second)
        for first, second in combinations(preferences.weekdays, 2)
        if second - first not in (1, 6)
    )
