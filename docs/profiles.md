# Basic Profile Increment

The first profile increment stores age, height in centimeters, weight in kilograms,
and an explicitly selected IANA time zone. It does not calculate calories, interpret
health conditions, or generate a fitness plan. Goals, training availability,
equipment, food preferences, allergies, and other planning inputs follow in separate
increments. These four fields alone must never trigger a personal plan.

Supported input bounds are application validation limits, not medical reference
ranges: age 18–120, height 50–300 cm, and weight 20–500 kg. Non-finite values,
booleans in numeric fields, missing data, and invalid time zones are rejected.
The server does not infer a user's time zone from its own clock or location.

Business validation and the immutable ProfileDetails value live in
backend/services/profiles.py and use only the Python standard library. HTTP schemas
and persistence must convert to/from these plain values; no ORM records may enter
the service.
