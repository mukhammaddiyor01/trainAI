"""Explicit catalog lookup, gram-based scaling, and unresolved planning boundaries."""

from dataclasses import dataclass
import math

from backend.services.catalogs import ExerciseDetails, FoodDetails, InvalidCatalog
from backend.services.food_preferences import FoodPreferencesDetails, validate_food_preferences
from backend.services.allergens import resolve_allergy_names


class UnknownCatalogItem(InvalidCatalog):
    """An ID is absent from the reviewed local catalog."""


class FoodSelectionUnavailable(ValueError):
    """Required food composition or allergy review is incomplete."""


def exercise_by_id(exercises: tuple[ExerciseDetails, ...], exercise_id: str) -> ExerciseDetails:
    if type(exercise_id) is str:
        for exercise in exercises:
            if exercise.id == exercise_id:
                return exercise
    raise UnknownCatalogItem("Choose a known exercise ID from the local catalog.")


def food_by_id(foods: tuple[FoodDetails, ...], food_id: str) -> FoodDetails:
    if type(food_id) is str:
        for food in foods:
            if food.id == food_id:
                return food
    raise UnknownCatalogItem("Choose a known food ID from the local catalog.")


@dataclass(frozen=True)
class FoodPortion:
    food_id: str
    preparation_state: str
    grams: float
    energy_kcal: float | None
    protein_g: float | None
    fat_g: float | None
    carbohydrate_g: float | None


def nutrition_for_grams(food: FoodDetails, grams: float) -> FoodPortion:
    if type(grams) not in (int, float) or not 0 < grams <= 10000 or not math.isfinite(grams):
        raise ValueError("Enter a portion above 0 and at most 10000 grams.")
    factor = grams / 100
    values = [None if value is None else value * factor for value in
              (food.energy_kcal, food.protein_g, food.fat_g, food.carbohydrate_g)]
    return FoodPortion(food.id, food.preparation_state, float(grams), *values)


def food_selection_blockers(food: FoodDetails, preferences: FoodPreferencesDetails) -> tuple[str, ...]:
    preferences = validate_food_preferences(preferences.diet, preferences.allergy_status, preferences.allergies,
                                             preferences.budget_level, preferences.prep_minutes, preferences.meal_times)
    blockers = []
    if preferences.allergy_status == "unsure":
        blockers.append("allergy_status_unsure")
    elif preferences.allergy_status == "listed":
        resolution = resolve_allergy_names(preferences.allergies)
        if resolution.unresolved_names:
            blockers.append("allergy_names_unresolved")
        # Recognizing a name does not complete ingredient or cross-contact review.
        blockers.append("allergy_mapping_unreviewed")
    if food.review_status != "composition_reviewed":
        blockers.append("composition_unreviewed")
    if food.ingredient_ids is None:
        blockers.append("ingredients_unknown")
    if food.diet_tags is None:
        blockers.append("diet_unknown")
    if food.allergen_tags is None:
        blockers.append("allergens_unknown")
    if any(value is None for value in (food.energy_kcal, food.protein_g, food.fat_g, food.carbohydrate_g)):
        blockers.append("nutrition_incomplete")
    return tuple(blockers)


def require_food_selection_review(food: FoodDetails, preferences: FoodPreferencesDetails) -> None:
    if food_selection_blockers(food, preferences):
        raise FoodSelectionUnavailable("Food selection requires reviewed composition, diet, nutrient, and allergy information.")
