"""Self-reported training preferences; no exercise prescription or calorie factors."""

from dataclasses import dataclass

EXPERIENCE_LEVELS = ("beginner", "intermediate", "advanced")
ACTIVITY_LEVELS = ("mostly_seated", "lightly_active", "moderately_active", "very_active")
EQUIPMENT_OPTIONS = ("dumbbells", "barbell", "resistance_bands", "bench", "pull_up_bar", "cable_machine", "weight_machines")
MIN_SESSION_MINUTES = 10
MAX_SESSION_MINUTES = 180


class InvalidTrainingPreferences(ValueError):
    """Preferences are incomplete or outside supported application limits."""


@dataclass(frozen=True)
class TrainingPreferencesDetails:
    experience: str
    activity: str
    equipment: tuple[str, ...]
    weekdays: tuple[int, ...]
    session_minutes: int


def validate_training_preferences(experience: str, activity: str,
                                  equipment: list[str] | tuple[str, ...],
                                  weekdays: list[int] | tuple[int, ...],
                                  session_minutes: int) -> TrainingPreferencesDetails:
    if type(experience) is not str or experience not in EXPERIENCE_LEVELS:
        raise InvalidTrainingPreferences("Choose a supported training experience level.")
    if type(activity) is not str or activity not in ACTIVITY_LEVELS:
        raise InvalidTrainingPreferences("Choose your usual activity outside planned workouts.")
    if type(equipment) not in (list, tuple) or len(equipment) > len(EQUIPMENT_OPTIONS):
        raise InvalidTrainingPreferences("Choose supported equipment, or leave it empty for bodyweight only.")
    if any(type(item) is not str or item not in EQUIPMENT_OPTIONS for item in equipment):
        raise InvalidTrainingPreferences("Choose only supported equipment.")
    if len(set(equipment)) != len(equipment):
        raise InvalidTrainingPreferences("Choose each equipment item only once.")
    if type(weekdays) not in (list, tuple) or not 1 <= len(weekdays) <= 7:
        raise InvalidTrainingPreferences("Choose one to seven available weekdays.")
    if any(type(day) is not int or not 1 <= day <= 7 for day in weekdays):
        raise InvalidTrainingPreferences("Weekdays must be integers from Monday (1) to Sunday (7).")
    if len(set(weekdays)) != len(weekdays):
        raise InvalidTrainingPreferences("Choose each weekday only once.")
    if type(session_minutes) is not int or not MIN_SESSION_MINUTES <= session_minutes <= MAX_SESSION_MINUTES:
        raise InvalidTrainingPreferences("Enter a session duration from 10 to 180 whole minutes.")
    return TrainingPreferencesDetails(experience, activity, tuple(sorted(equipment)),
                                      tuple(sorted(weekdays)), session_minutes)
