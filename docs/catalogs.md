# Reviewed Catalog Seeds

Catalogs are bundled local data, outside frontend/static. They are loaded explicitly
by feature code, never downloaded at startup. They do not generate a workout or
nutrition plan. Business values and equipment filtering use plain Python.

## Exercise source and rights

Six metadata records were selected from yuhonas/free-exercise-db at commit
f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5. The upstream repository declares the
Unlicense/public-domain dedication. The exact selected upstream records and
license notice are retained under data/catalogs/sources. No images were imported.

- [Upstream pinned source](https://github.com/yuhonas/free-exercise-db/tree/f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5)
- [Upstream license](https://github.com/yuhonas/free-exercise-db/blob/f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5/LICENSE.md)
- [Bundled metadata](../data/catalogs/exercises.json)
- [Selected source records](../data/catalogs/sources/free-exercise-db.json)
- [Retained notice](../data/catalogs/sources/LICENSE.free-exercise-db.txt)

Names, source level, force, and primary muscles are preserved. Source level is
an upstream classification, not a verified suitability assessment or training
prescription. Source instruction text is retained only as provenance evidence;
it is not presented as coaching or converted into sets, repetitions, or intensity.

The source's single equipment label is incomplete for some movements. A manual
review of the selected instructions adds bench for dumbbell bench press and the
bench-supported one-arm row, and pull_up_bar for pullups even though its upstream
label is body only. These reviewed requirements are explicit in every record.
Bodyweight squat, pushups, and plank require no named equipment in this seed.

## Validation boundary

Stable internal/source IDs, full commit revisions, pinned source URLs, reviewed
license, bounded fields, unique supported equipment, and primary muscles are
required. Unknown fields, missing requirements, duplicate IDs, ambiguous JSON,
non-finite numbers, oversized files, and unsupported schema versions fail closed.
An equipment query requires all items for a movement; a gym label grants nothing.
It returns candidates only, not a scheduled or prescribed workout.

Initial verification: four targeted exercise-catalog tests passed on 2026-10-31.


## USDA food nutrient seed

Four SR Legacy records were retrieved from the official USDA FoodData Central
API on 2026-10-31 using the documented public DEMO_KEY: 173944 (banana, raw),
171688 (apple with skin, raw), 168878 (regular enriched long-grain white rice,
cooked), and 168877 (regular enriched long-grain white rice, raw). Source data are
published under CC0-1.0. No private API key or user/profile data was supplied.
The seed keeps every exact description; source IDs and preparation state differ
for raw and cooked rice. It is a small historical reference, not a latest-product
or local-price database.

- [Official API guide and CC0 declaration](https://fdc.nal.usda.gov/api-guide/)
- [Official data-type documentation](https://fdc.nal.usda.gov/data-documentation/)
- [SR Legacy documentation, nutrient basis p. 12](https://www.ars.usda.gov/ARSUserFiles/80400525/Data/SR-Legacy/SR-Legacy_Doc.pdf)
- [Bundled food seed](../data/catalogs/foods.json)

Each record retains retrieval date, release label, source URL, and SHA-256 of the
complete retained API response under data/catalogs/sources/usda-sr-legacy. Loading
verifies the snapshot digest. Tests compare imported descriptions and amounts
against source nutrient IDs/units. Supported source IDs: 1008 (kcal), 1003 (protein
g), 1004 (fat g), 1005 (carbohydrate g), each per 100 g edible portion. Missing
values remain None; no macro formula fills absent energy or other nutrients.
Units must match IDs; kJ is never silently read as kcal.

Ingredient composition, diet tags, and allergen tags are explicitly unknown in
these nutrient-only records. An empty allergen set would claim knowledge the
source does not supply. None is retained instead. These records are not approved
for automatic food selection, allergy safety, or meal generation. A separate
composition/allergen review is required before that boundary can open.

Five targeted food-catalog tests passed on 2026-10-31, including source-value/unit
parity, raw/cooked identity, missing values, malformed metadata, and snapshot
corruption. No dependencies, schemas, HTTP endpoints, or private records changed.
