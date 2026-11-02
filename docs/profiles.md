# Basic Profile Increment

The first profile increment stores age, height in centimeters, weight in kilograms,
and an explicitly selected IANA time zone. It does not calculate calories, interpret
health conditions, or generate a fitness plan. Weight goals are implemented
separately; training availability and equipment are recorded in
[training preferences](training-preferences.md). Diet, reported allergies, and
meal timing are recorded in [food preferences](food-preferences.md).
The [adult energy method and explicit extra inputs](energy-estimation.md) are
now connected through private energy-preference storage, strict guarded APIs,
and an explicit input form. These four basic fields alone never trigger an
estimate or plan. Estimates read the current profile and calculation preferences
in one database snapshot; goal starting-weight snapshots remain unchanged.

Supported input bounds are application validation limits, not medical reference
ranges: age 18–120, height 50–300 cm, and weight 20–500 kg. Non-finite values,
booleans in numeric fields, missing data, and invalid time zones are rejected.
The server does not infer a user's time zone from its own clock or location.

Business validation and the immutable ProfileDetails value live in
backend/services/profiles.py and use only the Python standard library. HTTP schemas
and persistence must convert to/from these plain values; no ORM records may enter
the service.

## Persistence

Migration 0002 adds one profile per user, keyed by a foreign key to users.id.
SQL constraints enforce age, height, weight, and time-zone length bounds.
Persistence operations receive a server-selected owner UUID, return plain
ProfileDetails values, and use an atomic upsert for repeat saves. Integration
checks cover owner isolation, repeated updates, bounds, and foreign keys.

## Authenticated API

GET /api/profile and PUT /api/profile use the shared AuthenticatedAccount guard.
The API has no owner-ID path parameter and does not accept user_id or role in the
body. All persistence uses the guard's server-derived UUID. PUT additionally
requires the exact same Origin, bounded JSON (8192 bytes, 10 seconds), and a
strict ProfileInput schema before plain service validation. ProfileResponse exposes
only age, height_cm, weight_kg, and timezone. Reads return 404 until a profile exists.
Two-user HTTP checks verify that query spoofing and body mass assignment cannot
read or overwrite another user's profile. No plan or goal is created on save.

## Browser form

/profile redirects anonymous visitors and loads only the signed-in user's saved
values. The responsive form submits bounded JSON through the protected API,
disables fields during saving, times out after 15 seconds, and uses textContent
for messages. Saving, reload persistence, invalid-time-zone rejection, and mobile
layout were checked in a browser with a synthetic profile in a disposable cluster.
The invalid update did not replace the previously saved profile.
