"""Read only bundled catalog files; never download or import data at startup."""

import hashlib
import json
from pathlib import Path

from backend.services.catalogs import InvalidCatalog, NUTRIENT_UNITS, strings, validate_exercise, validate_food

CATALOG_ROOT = Path(__file__).resolve().parent.parent / "data" / "catalogs"
MAX_CATALOG_BYTES = 256 * 1024
MAX_CATALOG_RECORDS = 100


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidCatalog("Duplicate JSON keys are not allowed in a catalog.")
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidCatalog("Non-finite JSON numbers are not allowed in a catalog.")


def decode_catalog(raw: bytes) -> list[dict]:
    if not 1 <= len(raw) <= MAX_CATALOG_BYTES:
        raise InvalidCatalog("Catalog file exceeds the supported size.")
    try:
        envelope = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys, parse_constant=reject_constant)
    except (UnicodeError, ValueError, RecursionError):
        raise InvalidCatalog("Catalog JSON is invalid or ambiguous.") from None
    if type(envelope) is not dict or set(envelope) != {"schema_version", "records"}:
        raise InvalidCatalog("Catalog envelope fields are unsupported.")
    if type(envelope["schema_version"]) is not int or envelope["schema_version"] != 1:
        raise InvalidCatalog("Catalog schema version is unsupported.")
    records = envelope["records"]
    if type(records) is not list or not 1 <= len(records) <= MAX_CATALOG_RECORDS:
        raise InvalidCatalog("Catalog record count is unsupported.")
    return records


def load_records(filename: str, validator):
    try:
        with (CATALOG_ROOT / filename).open("rb") as source:
            raw = source.read(MAX_CATALOG_BYTES + 1)
    except OSError:
        raise InvalidCatalog("Bundled catalog is unavailable.") from None
    records = tuple(validator(record) for record in decode_catalog(raw))
    if len({record.id for record in records}) != len(records):
        raise InvalidCatalog("Catalog IDs must be unique.")
    return records


def load_exercises():
    exercises = load_records("exercises.json", validate_exercise)
    try:
        with (CATALOG_ROOT / "sources" / "free-exercise-db.json").open("rb") as source:
            raw = source.read(MAX_CATALOG_BYTES + 1)
        if len(raw) > MAX_CATALOG_BYTES:
            raise InvalidCatalog("Exercise source evidence is oversized.")
        evidence = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys, parse_constant=reject_constant)
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise InvalidCatalog("Exercise source evidence is unavailable or invalid.") from None
    if type(evidence) is not dict or set(evidence) != {"source_revision", "records"}:
        raise InvalidCatalog("Exercise source envelope is invalid.")
    records = evidence["records"]
    if type(records) is not list or len(records) != len(exercises):
        raise InvalidCatalog("Exercise source evidence count does not match.")
    sources = {}
    for record in records:
        if type(record) is not dict or type(record.get("id")) is not str or record["id"] in sources:
            raise InvalidCatalog("Exercise source IDs must be unique.")
        sources[record["id"]] = record
    for exercise in exercises:
        record = sources.get(exercise.source_id)
        if (record is None or evidence["source_revision"] != exercise.source_revision
                or record.get("name") != exercise.name or record.get("level") != exercise.source_level
                or record.get("force") != exercise.force
                or strings(record.get("primaryMuscles"), 8) != exercise.primary_muscles):
            raise InvalidCatalog("Exercise metadata does not match retained source evidence.")
    return exercises


def load_foods():
    foods = load_records("foods.json", validate_food)
    for food in foods:
        try:
            with (CATALOG_ROOT / "sources" / "usda-sr-legacy" / f"{food.source_id}.json").open("rb") as source:
                evidence = source.read(512 * 1024 + 1)
        except OSError:
            raise InvalidCatalog("Food source evidence is unavailable.") from None
        if len(evidence) > 512 * 1024 or hashlib.sha256(evidence).hexdigest() != food.source_sha256:
            raise InvalidCatalog("Food source evidence does not match its recorded digest.")
        try:
            original = json.loads(evidence.decode("utf-8"), object_pairs_hook=unique_keys, parse_constant=reject_constant)
        except (UnicodeError, ValueError, RecursionError):
            raise InvalidCatalog("Food source evidence is invalid JSON.") from None
        if (type(original) is not dict or original.get("fdcId") != food.source_id
                or original.get("description") != food.name or original.get("dataType") != "SR Legacy"):
            raise InvalidCatalog("Food identity does not match retained source evidence.")
        entries = original.get("foodNutrients")
        if type(entries) is not list or len(entries) > 500:
            raise InvalidCatalog("Food source nutrients are invalid or oversized.")
        observed = {}
        for entry in entries:
            if type(entry) is not dict or type(entry.get("nutrient")) is not dict:
                raise InvalidCatalog("Food source nutrient metadata is invalid.")
            nutrient = entry["nutrient"]
            key = nutrient.get("id")
            if type(key) is not int:
                raise InvalidCatalog("Food source nutrient ID is invalid.")
            if key not in NUTRIENT_UNITS:
                continue
            unit, amount = nutrient.get("unitName"), entry.get("amount")
            if (key in observed or type(unit) is not str or unit.lower() != NUTRIENT_UNITS[key]
                    or (amount is not None and type(amount) not in (int, float))):
                raise InvalidCatalog("Food source nutrient units or values are invalid.")
            observed[key] = amount
        expected = {1008: food.energy_kcal, 1003: food.protein_g, 1004: food.fat_g, 1005: food.carbohydrate_g}
        if any(observed.get(key) != amount for key, amount in expected.items()):
            raise InvalidCatalog("Food nutrient values do not match retained source evidence.")
    return foods
