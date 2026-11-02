"""Explicit adult energy-method choices, independent of account identity and training."""

from dataclasses import dataclass

EQUATION_SEX_OPTIONS = ("male", "female", "unsure")
ENERGY_ACTIVITY_CATEGORIES = ("inactive", "low_active", "active", "very_active", "unsure")
ENERGY_CONTEXTS = ("general_adult", "pregnant", "breastfeeding", "clinical", "unsure")


class InvalidEnergyPreferences(ValueError):
    """A calculation choice is missing, coerced, or unsupported."""


@dataclass(frozen=True)
class EnergyPreferencesDetails:
    equation_sex: str
    activity_category: str
    context: str


def validate_energy_preferences(equation_sex: str, activity_category: str,
                                context: str) -> EnergyPreferencesDetails:
    for value, choices, message in (
        (equation_sex, EQUATION_SEX_OPTIONS, "Choose a supported equation sex or unsure."),
        (activity_category, ENERGY_ACTIVITY_CATEGORIES, "Choose a whole-day energy activity category or unsure."),
        (context, ENERGY_CONTEXTS, "Choose an energy calculation context or unsure."),
    ):
        if type(value) is not str or value not in choices:
            raise InvalidEnergyPreferences(message)
    return EnergyPreferencesDetails(equation_sex, activity_category, context)
