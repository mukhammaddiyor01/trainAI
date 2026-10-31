"""Read only bundled catalog files; never download or import data at startup."""

import hashlib
import json
from pathlib import Path

from backend.services.catalogs import InvalidCatalog, validate_exercise, validate_food

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
    return load_records("exercises.json", validate_exercise)


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
    return foods
