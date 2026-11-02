"""Bounded exact food-allergy name resolution; not diagnosis or food approval."""

from dataclasses import dataclass
from types import MappingProxyType

from backend.services.food_preferences import MAX_ALLERGIES, InvalidFoodPreferences, normalize_allergy_name

MAPPING_VERSION = "fda-major-terms-2026-11-02-v1"
MAPPING_SOURCE_URL = "https://www.fda.gov/media/117410/download"
MAPPING_SOURCE_EDITION = "Edition 5, January 2025; A.1-A.2, B.9, B.11, C.10-C.11"
MAPPING_REVIEWED_ON = "2026-11-02"

# This authored subset deliberately leaves species, translations, and ambiguous names unresolved.
ALLERGEN_GROUPS = (
    ("milk", ("milk",)),
    ("egg", ("egg", "eggs")),
    ("fish", ("fish",)),
    ("crustacean_shellfish", ("crustacean shellfish",)),
    ("tree_nuts", ("tree nut", "tree nuts")),
    ("peanut", ("peanut", "peanuts")),
    ("wheat", ("wheat",)),
    ("soy", ("soy", "soya", "soybean", "soybeans")),
    ("sesame", ("sesame",)),
)


def reviewed_allergen_aliases():
    aliases = {}
    identifiers = set()
    for identifier, names in ALLERGEN_GROUPS:
        if identifier in identifiers or not names:
            raise ValueError("Allergen groups require unique IDs and reviewed names.")
        identifiers.add(identifier)
        for name in names:
            if name != normalize_allergy_name(name) or name in aliases:
                raise ValueError("Allergen aliases must be normalized and unambiguous.")
            aliases[name] = identifier
    return MappingProxyType(aliases)


@dataclass(frozen=True)
class AllergyResolution:
    allergen_ids: tuple[str, ...]
    unresolved_names: tuple[str, ...]
    mapping_version: str = MAPPING_VERSION


def resolve_allergy_names(names: list[str] | tuple[str, ...]) -> AllergyResolution:
    if type(names) not in (list, tuple) or len(names) > MAX_ALLERGIES:
        raise InvalidFoodPreferences("Enter up to 20 reported food allergies.")
    normalized = tuple(normalize_allergy_name(name) for name in names)
    if len(set(normalized)) != len(normalized):
        raise InvalidFoodPreferences("List each reported allergy only once.")
    aliases = reviewed_allergen_aliases()
    resolved = tuple(sorted({aliases[name] for name in normalized if name in aliases}))
    unresolved = tuple(sorted(name for name in normalized if name not in aliases))
    return AllergyResolution(resolved, unresolved)
