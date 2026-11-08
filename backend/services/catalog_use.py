"""Explicit catalog lookup, gram-based scaling, and unresolved planning boundaries."""

from dataclasses import dataclass
import math

from backend.services.catalogs import ExerciseDetails, FoodDetails, InvalidCatalog
from backend.services.food_preferences import FoodPreferencesDetails, validate_food_preferences
from backend.services.allergens import resolve_allergy_names
from backend.services.movement_limitations import MovementLimitationsDetails, validate_movement_limitations
from backend.services.training_preferences import TrainingPreferencesDetails, validate_training_preferences


class UnknownCatalogItem(InvalidCatalog):
    """An ID is absent from the reviewed local catalog."""


class FoodSelectionUnavailable(ValueError):
    """Required food composition or allergy review is incomplete."""


class ExerciseSelectionUnavailable(ValueError):
    """An exercise cannot enter an automatic workout selector yet."""


def exercise_by_id(exercises: tuple[ExerciseDetails, ...], exercise_id: str) -> ExerciseDetails:
    if type(exercise_id) is str:
        for exercise in exercises:
            if exercise.id == exercise_id:
                return exercise
    raise UnknownCatalogItem("Choose a known exercise ID from the local catalog.")


def exercise_selection_blockers(
    exercises: tuple[ExerciseDetails, ...],
    exercise_id: str,
    preferences: TrainingPreferencesDetails | None,
    limitations: MovementLimitationsDetails | None,
) -> tuple[str, ...]:
    """Explain unresolved prerequisites without treating source metadata as a prescription."""
    exercise = exercise_by_id(exercises, exercise_id)
    blockers = []
    if preferences is None:
        blockers.append("training_preferences_missing")
    else:
        if type(preferences) is not TrainingPreferencesDetails:
            raise ValueError("Validated training preferences are required.")
        preferences = validate_training_preferences(
            preferences.experience, preferences.activity, preferences.equipment,
            preferences.weekdays, preferences.session_minutes,
        )
        if not set(exercise.required_equipment) <= set(preferences.equipment):
            blockers.append("equipment_unavailable")
    if limitations is None:
        blockers.append("movement_answer_missing")
    else:
        if type(limitations) is not MovementLimitationsDetails:
            raise ValueError("Validated movement limitations are required.")
        status = validate_movement_limitations(limitations.status).status
        if status == "unsure":
            blockers.append("movement_answer_unsure")
        elif status == "needs_adaptation":
            blockers.append("adaptation_review_required")
    # None of the six metadata seeds has an exercise-specific suitability or dosage review.
    blockers.append("exercise_prescription_unreviewed")
    return tuple(blockers)


def require_exercise_selection_review(
    exercises: tuple[ExerciseDetails, ...],
    exercise_id: str,
    preferences: TrainingPreferencesDetails | None,
    limitations: MovementLimitationsDetails | None,
) -> None:
    if exercise_selection_blockers(exercises, exercise_id, preferences, limitations):
        raise ExerciseSelectionUnavailable("Exercise selection requires a reviewed prescription and complete inputs.")


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


@dataclass(frozen=True)
class FoodPortionTotals:
    portions: tuple[FoodPortion, ...]
    energy_kcal: float | None
    protein_g: float | None
    fat_g: float | None
    carbohydrate_g: float | None


def nutrition_for_portions(
    foods: tuple[FoodDetails, ...],
    portions: list[tuple[str, float]] | tuple[tuple[str, float], ...],
) -> FoodPortionTotals:
    """Sum explicit (food ID, grams) rows against a validated catalog, without selecting foods."""
    if type(portions) not in (list, tuple) or not 1 <= len(portions) <= 50:
        raise ValueError("Provide between 1 and 50 explicit food portions.")
    resolved = []
    for row in portions:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError("Each portion requires exactly a food ID and grams.")
        food_id, grams = row
        resolved.append(nutrition_for_grams(food_by_id(foods, food_id), grams))
    totals = []
    for nutrient in ("energy_kcal", "protein_g", "fat_g", "carbohydrate_g"):
        values = tuple(getattr(portion, nutrient) for portion in resolved)
        # A partial subtotal must not appear to be a complete nutrient total.
        totals.append(None if any(value is None for value in values) else math.fsum(values))
    return FoodPortionTotals(tuple(resolved), *totals)


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
