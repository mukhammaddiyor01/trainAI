"""Plain catalog values and strict metadata validation; no HTTP, ORM, or network."""

from dataclasses import dataclass
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
