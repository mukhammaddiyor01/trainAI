# Daily Weight Logging Boundary

Decision recorded 2026-11-11. A weight entry is a user-recorded measurement on
an explicit calendar date in the saved profile's IANA time zone. It is an
observation, not a workout or nutrition plan, body-composition estimate, or
automatic update to the basic profile.

## Input and history rules

- The user supplies an ISO `YYYY-MM-DD` local date and a finite weight in kg.
  The existing 20–500 kg application bound is reused for consistency; it does
  not identify a medically suitable weight.
- The date must not be later than the current calendar date in the owner's
  saved profile time zone. The server clock's date and browser time zone are not
  substitutes. The service receives the owner's current local date explicitly
  so its rule is deterministic and testable offline.
- At most one current entry exists per owner and local date. An explicit edit
  can replace that day's value; a missing date is unknown, never zero or an
  assumed missed measurement. The recorded date does not shift if the profile
  time zone later changes.
- An entry does not rewrite profile weight, goal starting weight, a pending
  proposal, or an approved calorie target. Those have separate owner actions
  and version rules. A single entry cannot establish a trend, adherence,
  fat/muscle change, or a reason to revise calories.

## Implemented flow

Migration 0010 adds `weight_entries` with a composite owner/date primary key,
bounded kg check, and cascading profile foreign key. `PUT /api/weight-entries`
validates a strict two-field JSON object up to 2048 bytes, requires a signed-in
account and same Origin, and inserts or corrects the selected date. The server
uses the saved profile time zone to reject future dates. `GET /api/weight-entries`
returns at most 30 owner entries, newest date first, with only date and kg.
Both endpoints reject query parameters. The responsive `/weight-log` page is
private, profile-first, and shows the same bounded history. It uses local assets
and the existing private response policies. Tests use synthetic accounts in a
disposable PostgreSQL cluster; measurements are not logged.
