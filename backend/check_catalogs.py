"""Explicit offline operator check: python -m backend.check_catalogs."""

from backend.catalogs import load_exercises, load_foods
from backend.services.catalogs import InvalidCatalog


def main() -> int:
    try:
        exercises = load_exercises()
        foods = load_foods()
    except InvalidCatalog:
        print("Catalog verification failed. Review bundled records and source evidence.")
        return 1
    print("Bundled catalog contracts and source evidence verified offline.")
    print(f"Exercise metadata records: {len(exercises)}")
    print(f"Food nutrient records: {len(foods)}")
    print("Food selection: unavailable; ingredient, diet, and allergen review is incomplete.")
    print("No plans, daily targets, database changes, or external requests were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
