"""Explicit offline operator check: python -m backend.check_catalogs."""

from backend.catalogs import load_exercises, load_foods
from backend.services.catalogs import InvalidCatalog
from backend.services.allergens import MAPPING_VERSION, reviewed_allergen_aliases


def main() -> int:
    try:
        exercises = load_exercises()
        foods = load_foods()
        aliases = reviewed_allergen_aliases()
    except (InvalidCatalog, ValueError):
        print("Catalog verification failed. Review bundled records and source evidence.")
        return 1
    print("Bundled catalog contracts and source evidence verified offline.")
    print(f"Exercise metadata records: {len(exercises)}")
    print(f"Food nutrient records: {len(foods)}")
    print(f"Reviewed allergy-name groups: {len(set(aliases.values()))}")
    print(f"Reviewed allergy terms: {len(aliases)}")
    print(f"Allergy mapping version: {MAPPING_VERSION}")
    pending = sum(food.review_status != "composition_reviewed" for food in foods)
    print(f"Food composition reviews pending: {pending}")
    print("Food selection: unavailable; ingredient, diet, and allergen review is incomplete.")
    print("No plans, daily targets, database changes, or external requests were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
