"""Validate reported food preferences without prescribing meals or calorie targets."""

from dataclasses import dataclass
import re

DIETS = ("mixed", "vegetarian", "vegan")
ALLERGY_STATUSES = ("unsure", "none_reported", "listed")
BUDGET_LEVELS = ("economical", "standard", "flexible")
MAX_ALLERGIES = 20
MAX_ALLERGY_LENGTH = 64
MAX_MEALS = 8
MAX_PREP_MINUTES = 180


class InvalidFoodPreferences(ValueError):
    """Reported preferences are incomplete or exceed application input limits."""


@dataclass(frozen=True)
class FoodPreferencesDetails:
    diet: str
    allergy_status: str
    allergies: tuple[str, ...]
    budget_level: str
    prep_minutes: int
    meal_times: tuple[str, ...]


def validate_food_preferences(diet: str, allergy_status: str,
                              allergies: list[str] | tuple[str, ...], budget_level: str,
                              prep_minutes: int, meal_times: list[str] | tuple[str, ...]) -> FoodPreferencesDetails:
    if type(diet) is not str or diet not in DIETS:
        raise InvalidFoodPreferences("Choose mixed, vegetarian, or vegan meals.")
    if type(allergy_status) is not str or allergy_status not in ALLERGY_STATUSES:
        raise InvalidFoodPreferences("Choose an explicit food allergy status.")
    if type(allergies) not in (list, tuple) or len(allergies) > MAX_ALLERGIES:
        raise InvalidFoodPreferences("Enter up to 20 reported food allergies.")
    names = []
    for name in allergies:
        if type(name) is not str or not 1 <= len(name) <= MAX_ALLERGY_LENGTH or not name.isprintable():
            raise InvalidFoodPreferences("Use 1 to 64 printable characters per allergy name.")
        cleaned = " ".join(name.strip().split()).casefold()
        if not cleaned or len(cleaned) > MAX_ALLERGY_LENGTH:
            raise InvalidFoodPreferences("Enter a non-empty allergy name of up to 64 characters.")
        names.append(cleaned)
    if len(set(names)) != len(names):
        raise InvalidFoodPreferences("List each reported allergy only once.")
    if (allergy_status == "listed") != bool(names):
        raise InvalidFoodPreferences("List allergies only when choosing 'I have food allergies'.")
    if type(budget_level) is not str or budget_level not in BUDGET_LEVELS:
        raise InvalidFoodPreferences("Choose an economical, standard, or flexible spending preference.")
    if type(prep_minutes) is not int or not 0 <= prep_minutes <= MAX_PREP_MINUTES:
        raise InvalidFoodPreferences("Enter 0 to 180 whole minutes for preparation per meal.")
    if type(meal_times) not in (list, tuple) or not 1 <= len(meal_times) <= MAX_MEALS:
        raise InvalidFoodPreferences("Choose one to eight meal times.")
    if any(type(time) is not str or re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", time) is None
           for time in meal_times):
        raise InvalidFoodPreferences("Use 24-hour meal times in HH:MM format.")
    if len(set(meal_times)) != len(meal_times):
        raise InvalidFoodPreferences("Choose each meal time only once.")
    return FoodPreferencesDetails(diet, allergy_status, tuple(sorted(names)), budget_level,
                                   prep_minutes, tuple(sorted(meal_times)))
