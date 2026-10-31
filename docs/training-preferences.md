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


## Protected API

GET/PUT /api/training-preferences derive ownership from the shared session guard.
Writes require the exact same Origin, bounded JSON up to 4096 bytes, strict types,
exactly five allowlisted fields, and plain service validation. A saved basic
profile is required (409 if absent); GET returns 404 until preferences are saved.
Responses contain only experience, activity, equipment, weekdays, and session_minutes.
Unknown owner/role/storage fields fail validation. Existing rate, time, response,
and browser security limits apply. Invalid saves preserve prior values.
Five targeted API checks passed in disposable PostgreSQL, including two-user
isolation, malformed/oversized JSON, revoked access, and response allowlisting.


## Browser flow

/training-preferences redirects anonymous visitors to /login and accounts without
profiles to /profile. Account and goal pages link to the form. Saved selections
are rendered by the server; empty selections do not invent user preferences.
Native labeled selects, grouped checkboxes, and an integer duration input support
keyboard use. The form rejects no selected days before requesting a save. Writes
use a POST fallback action (no private query fields) and JavaScript PUT, with a
15-second timeout, disabled fields during saving, textContent feedback, and stale
success clearing on edits. A successful save reloads stored server values.

Two targeted page tests passed. Browser verification used synthetic accounts in
a disposable cluster: profile-first redirect, empty-weekday rejection, bodyweight
save/reload, equipment/duration changes, saved-value persistence, stale-success
clearing, desktop/mobile inspection, and logout redirect. No horizontal overflow
was found at inspected effective widths of 1163 and 354 CSS pixels (requested
1280/390 viewport overrides; browser zoom changes effective sizes). Browser
console inspection returned no warnings or errors. The temporary cluster was
stopped and removed. All 83 application tests passed in isolated PostgreSQL on
2026-10-31, including migration round trips. No dependency changes were needed.
