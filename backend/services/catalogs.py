"""Plain catalog values and strict metadata validation; no HTTP, ORM, or network."""

from dataclasses import dataclass
import math
import re

from backend.services.training_preferences import EQUIPMENT_OPTIONS


class InvalidCatalog(ValueError):
    """Catalog metadata is missing, ambiguous, or unsupported."""


def record_fields(record: dict, fields: set[str]) -> None:
    if type(record) is not dict or set(record) != fields:
        raise InvalidCatalog("Catalog records must contain exactly the documented fields.")


def text(value: str, maximum: int = 160) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum or not value.isprintable() or not value.strip():
        raise InvalidCatalog("Catalog text is missing or exceeds supported limits.")
    return value


def strings(values: list[str] | tuple[str, ...], maximum: int, allowed=None) -> tuple[str, ...]:
    if type(values) not in (list, tuple) or len(values) > maximum:
        raise InvalidCatalog("Catalog selections must be bounded lists.")
    result = tuple(text(value, 64) for value in values)
    if len(set(result)) != len(result) or (allowed is not None and any(value not in allowed for value in result)):
        raise InvalidCatalog("Catalog selections contain duplicate or unsupported values.")
    return tuple(sorted(result))


@dataclass(frozen=True)
class ExerciseDetails:
    id: str
    name: str
    required_equipment: tuple[str, ...]
    force: str
    source_level: str
    primary_muscles: tuple[str, ...]
    source_id: str
    source_revision: str
    source_url: str
    license: str
    equipment_review: str


def validate_exercise(record: dict) -> ExerciseDetails:
    record_fields(record, set(ExerciseDetails.__dataclass_fields__))
    exercise_id = text(record["id"], 100)
    if re.fullmatch(r"exercise-[a-z0-9]+(?:-[a-z0-9]+)*", exercise_id) is None:
        raise InvalidCatalog("Use a stable supported exercise ID.")
    source_id = text(record["source_id"], 100)
    revision = text(record["source_revision"], 40)
    if re.fullmatch(r"[A-Za-z0-9_-]+", source_id) is None or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise InvalidCatalog("Exercise provenance requires a source ID and full commit revision.")
    expected_url = f"https://github.com/yuhonas/free-exercise-db/blob/{revision}/exercises/{source_id}.json"
    if record["source_url"] != expected_url or record["license"] != "Unlicense":
        raise InvalidCatalog("Exercise source URL or reviewed license is unsupported.")
    if record["force"] not in ("push", "pull", "static") or record["source_level"] not in ("beginner", "intermediate", "expert"):
        raise InvalidCatalog("Exercise source classifications are unsupported.")
    muscles = strings(record["primary_muscles"], 8)
    if not muscles:
        raise InvalidCatalog("A sourced primary muscle is required.")
    return ExerciseDetails(exercise_id, text(record["name"]),
                           strings(record["required_equipment"], 7, EQUIPMENT_OPTIONS),
                           record["force"], record["source_level"], muscles, source_id, revision,
                           expected_url, "Unlicense", text(record["equipment_review"], 500))


def exercises_for_equipment(exercises: tuple[ExerciseDetails, ...], equipment: list[str] | tuple[str, ...]) -> tuple[ExerciseDetails, ...]:
    available = set(strings(equipment, 7, EQUIPMENT_OPTIONS))
    return tuple(exercise for exercise in exercises if set(exercise.required_equipment) <= available)


NUTRIENT_UNITS = {1008: "kcal", 1003: "g", 1004: "g", 1005: "g"}


@dataclass(frozen=True)
class FoodDetails:
    id: str
    name: str
    preparation_state: str
    energy_kcal: float | None
    protein_g: float | None
    fat_g: float | None
    carbohydrate_g: float | None
    ingredient_ids: tuple[str, ...] | None
    diet_tags: tuple[str, ...] | None
    allergen_tags: tuple[str, ...] | None
    review_status: str
    source_id: int
    source_release: str
    source_url: str
    source_sha256: str
    license: str
    retrieved_on: str


def validate_food(record: dict) -> FoodDetails:
    record_fields(record, {"id", "name", "preparation_state", "basis_g", "nutrients",
                           "ingredient_ids", "diet_tags", "allergen_tags", "review_status",
                           "source_id", "source_release", "source_url", "source_sha256", "license", "retrieved_on"})
    food_id = record["source_id"]
    if type(food_id) is not int or not 1 <= food_id <= 99999999 or record["id"] != f"food-fdc-{food_id}":
        raise InvalidCatalog("Food IDs must match the sourced USDA record.")
    expected_url = f"https://fdc.nal.usda.gov/food-details/{food_id}/nutrients"
    if record["source_url"] != expected_url or record["source_release"] != "SR Legacy April 2018" or record["license"] != "CC0-1.0":
        raise InvalidCatalog("Food provenance or reviewed license is unsupported.")
    digest = text(record["source_sha256"], 64)
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise InvalidCatalog("Food source evidence requires a SHA-256 digest.")
    from datetime import date
    try:
        retrieved_on = date.fromisoformat(text(record["retrieved_on"], 10)).isoformat()
    except ValueError:
        raise InvalidCatalog("A valid source retrieval date is required.") from None
    if type(record["basis_g"]) is not int or record["basis_g"] != 100:
        raise InvalidCatalog("Food nutrient values must use a 100-gram edible basis.")
    if record["preparation_state"] not in ("raw", "cooked"):
        raise InvalidCatalog("Food preparation state must be explicit.")
    # The first seed is nutrition-only: absence of composition data is not evidence of safety.
    if record["review_status"] != "nutrition_only" or any(record[key] is not None for key in ("ingredient_ids", "diet_tags", "allergen_tags")):
        raise InvalidCatalog("This seed requires unresolved composition metadata to remain unknown.")
    nutrients = record["nutrients"]
    if type(nutrients) is not list or len(nutrients) > 4:
        raise InvalidCatalog("Only the four documented nutrient IDs are supported.")
    values = {}
    for nutrient in nutrients:
        record_fields(nutrient, {"id", "unit", "amount"})
        key = nutrient["id"]
        if type(key) is not int or key not in NUTRIENT_UNITS or key in values:
            raise InvalidCatalog("Nutrient IDs must be supported and unique.")
        if type(nutrient["unit"]) is not str or nutrient["unit"].lower() != NUTRIENT_UNITS[key]:
            raise InvalidCatalog("Nutrient units must match the documented source ID.")
        amount = nutrient["amount"]
        if amount is not None:
            maximum = 1000 if key == 1008 else 100
            if type(amount) not in (int, float) or not 0 <= amount <= maximum or not math.isfinite(amount):
                raise InvalidCatalog("Nutrient values must be finite supported amounts or unknown.")
            amount = float(amount)
        values[key] = amount
    return FoodDetails(record["id"], text(record["name"], 200), record["preparation_state"],
                       values.get(1008), values.get(1003), values.get(1004), values.get(1005),
                       None, None, None, "nutrition_only", food_id, record["source_release"],
                       expected_url, digest, "CC0-1.0", retrieved_on)
