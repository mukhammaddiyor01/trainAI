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


## Lookup, portion units, and planning boundary

Use exact internal IDs through exercise_by_id/food_by_id; unknown IDs and free
text do not substitute for reviewed records. nutrition_for_grams scales each
available source nutrient by grams/100. It accepts finite positive mass up to
10000 g (an application input bound), returns the source food/preparation identity,
and preserves missing nutrients as None. It does not infer a household serving,
convert cooked/raw mass, compute daily needs, or create a plan.

food_selection_blockers records unresolved composition, ingredient, diet, allergen,
and nutrient data. Unsure allergy status and listed names without reviewed mapping
also block selection. require_food_selection_review rejects all four current food
seeds even when the user reports no known allergies. No clinical safety or actual
allergen filtering is claimed; the gate prevents incomplete data entering a future
selector. Composition review and a complete selector remain separate future work.
Five targeted use-rule tests passed: known/unknown IDs, source-based gram scaling,
raw/cooked separation, missing nutrients, strict portion inputs, and blocked seeds.


Source-link verification found the candidate USDA web detail routes returned 404.
Food source URLs therefore use the official documented /fdc/v1/food/{fdcId} API
with its public demonstration key, matching the responses actually retrieved.
DEMO_KEY is explicitly public in USDA's guide, not a user's private credential;
clicking these source links is subject to USDA's public-demo rate limits. Runtime
catalog loading is offline and never follows these links.


## Explicit offline check

Run `.venv/bin/python -m backend.check_catalogs`. It validates both local catalogs,
compares exercise source IDs/revisions and preserved metadata with selected source
evidence, and checks food snapshot hashes plus imported identity/nutrient/unit
parity. Exit 0 means the bundled contracts and evidence pass; it does not mean food selection or planning is available. Failure
returns exit 1 with a generic diagnostic. The command reports 6 exercise records,
4 nutrient records, and unavailable food selection. It does not read DATABASE_URL,
connect to a database, fetch URLs, alter a schema, or run automatically at startup.
Two operator-check tests passed, including socket denial and safe failure output.


## Milestone verification — 2026-10-31

All 17 catalog checks passed. The complete isolated PostgreSQL application suite
then passed 116 tests, none skipped, including migration downgrade/upgrade.
`pip check` found no broken requirements. No dependencies or schema changes were
introduced. The configured database remains at 0005 and was not used for catalog
checks. No UI or HTTP endpoint changed, so browser verification was not repeated.
The historical dependency-advisory audit was not rerun.

Next: review ingredient/diet/allergen composition evidence and explicit allergy
mapping before opening food selection; review calculation inputs/methods before
setting daily targets. Exercise prescriptions and plan generation require their
own reviewed rules. Catalog presence alone must not trigger either feature.


Final source-audit refinement: food loading also compares source identity, source
nutrient IDs, units, and amounts with the retained response. Editing a prepared
nutrient amount or name while keeping the original snapshot hash now fails.
The new regression passed; all 116 application checks passed after this change.


## Exact allergy-name readiness — 2026-11-02

The [bounded name resolver](allergen-names.md) recognizes 15 exact English terms
in nine reviewed groups and retains every unmatched name. Food readiness adds
allergy_names_unresolved for any unknown term, including partially recognized
lists. Recognized names still retain allergy_mapping_unreviewed: name recognition
has not completed ingredient/cross-contact review. All existing composition,
ingredient, diet, allergen, and nutrient blockers remain active.

The offline check validates registry ambiguity/normalization, prints its version
and term/group counts, and reports four pending composition reviews without
processing user data. Inspection of retained USDA responses found no ingredient
declarations or root-level allergen fields. No composition approval was inferred.
The full isolated PostgreSQL suite passed 124 tests on 2026-11-02, none skipped.
No new dependencies, database migrations, UI, or HTTP contracts were introduced.
