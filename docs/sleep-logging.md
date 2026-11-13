# Daily Sleep Duration Logging Boundary

Decision recorded 2026-11-13. A sleep entry is a user's reported duration for
an explicit calendar date in the saved profile's IANA time zone. The date is the
day the user assigns to the sleep period. It is not inferred from bedtime,
wake time, the browser clock, or the server's local date.

- Store whole minutes from 0 to 1440 (24 hours). This is an application input
  bound, not a healthy-sleep range. Zero is an explicit report; an absent date
  remains unknown and must never be filled with zero.
- Reject dates later than today in the owner's saved time zone. Keep a recorded
  date unchanged if that zone later changes. Permit one current entry per owner
  and date; saving the same date explicitly corrects its duration.
- Show no diagnosis, sleep quality score, fatigue inference, calorie change,
  workout adjustment, or plan revision from this value. A duration alone cannot
  establish why someone slept less or more.
- Owner identity comes from the session. Persistence, API, and page use bounded
  reads and strict validation. Tests use synthetic accounts and a disposable
  PostgreSQL cluster; private durations do not enter logs or fixtures.

## Implemented flow

Migration 0011 adds `sleep_entries` with an owner/date primary key, 0–1440 minute
SQL check, and cascading profile foreign key. `PUT /api/sleep-entries` accepts
only local date and whole minutes in at most 2048 JSON bytes, requires a session
and exact Origin, and corrects an existing date atomically. `GET` returns at most
30 newest owner entries with only those two fields. Both endpoints reject query
parameters. The profile-first `/sleep-log` page uses separate hours and minutes
inputs, shows recent entries, and supports explicit correction. No other saved
profile, target, or plan record changes.
