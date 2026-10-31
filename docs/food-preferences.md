# Food Preferences

This onboarding increment records user intent. It does not select foods, diagnose
allergies, calculate calories, or declare a meal safe. Plain Python validation
has no HTTP, ORM, model, network, or camera dependencies.

## Field meanings

- Diet: mixed (no vegetarian/vegan restriction), vegetarian (no meat or fish;
  dairy/eggs may be included), or vegan (no animal-derived foods). These are
  product preference definitions; ingredient filtering arrives with reviewed catalogs.
- Allergy status: unsure, none_reported, or listed. No answer is inferred from
  an empty list. Listed requires at least one name; the other states require an
  empty list. None_reported records a user statement, not verified absence.
- Allergies: up to 20 printable names, each 1–64 characters. Surrounding/repeated
  whitespace is normalized, names are case-folded, duplicates rejected. Names
  may describe allergies beyond a fixed regional checklist. No synonym mapping,
  diagnosis, intolerance interpretation, or ingredient-safety inference is performed.
- Budget level: economical, standard, or flexible, chosen by the user. This is
  spending style, not a monetary amount, currency, verified price, or cost guarantee.
- Preparation: 0–180 whole minutes available per meal; zero allows no-cook choices.
- Meal times: 1–8 unique HH:MM values on a 24-hour clock, sorted chronologically.
  They refer to local clock times in the saved profile's IANA zone, not UTC instants.
  Changing the profile zone retains clock times in the newly selected zone.
  Meal frequency and preparation bounds are application limits, not recommendations.

Validated collections are copied to immutable tuples. Missing/invalid fields,
ambiguous allergy states, booleans/numeric-string durations, malformed times,
control characters, duplicate entries, and unbounded collections fail cleanly.

## Future planning boundary

Before meal generation, ingredient/allergen metadata and diet definitions must
be checked against sourced catalogs. Unsure status and unresolved reported names
must block automatic food selection, not silently become unrestricted eating.
Missing ingredient/allergen information remains unknown. An AI must not infer
allergen safety from free text or a diet label. Current preferences do not
constitute complete calculation inputs or medical clearance.


## Persistence

Migration 0005 adds one row per basic profile, with an owner primary/foreign key,
cascading deletion, and atomic full-row upserts. Concurrent identical saves keep
one row. No preference history is retained. PostgreSQL checks constrain choices,
preparation bounds, allergy-state/list consistency, array dimensions/counts/nulls,
and meal-minute bounds. Meal times are stored as integer minutes after midnight
and returned as canonical HH:MM strings. Text normalization and duplicate/name
validation remain in the plain service and are repeated before persistence.

Four targeted disposable PostgreSQL tests passed: round trips and owner isolation,
full replacement and invalid-update preservation, concurrent retries, SQL bounds,
and migration/model parity. Disposable migration downgrade/upgrade passed. The
configured application database remains at 0004 at this increment.


## Protected API

GET/PUT /api/food-preferences expose only the six preference fields. Shared guards
resolve the owner from the session; writes require the exact same Origin. The
8192-byte bounded JSON reader, strict schema, and plain service reject unknown
owner/role/time-zone/storage fields, coercion, malformed data, and inconsistent
allergy states. A basic profile is required before saving (409); missing saved
preferences return 404. Existing API rate/time/response limits apply. Invalid
updates preserve prior values; errors never echo reported allergy text.
Five targeted API tests passed in disposable PostgreSQL, including two-user
isolation, revocation, canonical response values, and malformed/oversized requests.
