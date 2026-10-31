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
Food data and its separate review boundary follow in a later small increment.
