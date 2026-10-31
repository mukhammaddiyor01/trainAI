# Training Preferences

Plain Python validation records self-reported preferences independently of HTTP,
SQLAlchemy, or model libraries. This is not an exercise prescription or a calorie
calculation; no activity multipliers or generated workouts are attached.

- Experience: beginner, intermediate, or advanced (self-selected).
- Usual activity outside planned workouts: mostly_seated, lightly_active,
  moderately_active, or very_active. These are descriptive labels only.
- Available equipment: dumbbells, barbell, resistance_bands, bench, pull_up_bar,
  cable_machine, or weight_machines. An empty list means bodyweight only.
  Access to a gym must not imply access to every equipment item.
- Available weekdays: one to seven unique integer days, Monday=1 through Sunday=7.
  Availability is not a recommendation to train every selected day.
- Session duration: an integer from 10 to 180 minutes. These are supported input
  limits, not medically recommended durations.

Duplicates, unknown choices, malformed collections, coercible numeric strings,
boolean days/durations, and non-integer durations are rejected. Valid collections
are sorted and copied into immutable tuples, preventing later caller mutation.
## Persistence

Migration 0004 adds one owner-keyed row per basic profile, with a cascading
foreign key and SQL checks for choices, available days, equipment, and duration.
Atomic upserts replace the complete selection; concurrent retries keep one row.
Equipment and weekdays use bounded seven-bit sets in storage, so duplicate
selections cannot exist in a row. Bit positions are fixed in the persistence
module and must not change without a migration. Plain service/API values remain
named equipment and Monday-based weekday integers. Bodyweight is the empty set.
No preference history is retained yet. API and browser controls follow separately.
