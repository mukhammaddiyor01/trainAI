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

## Implementation order

First add a plain immutable validated value. Then add an owner-keyed PostgreSQL
table and explicit migration, guarded bounded API, and private responsive form
in separate verified increments. Storage and HTTP must derive owner identity
from the session, reject forged owner fields, keep list reads bounded, and avoid
logging measurements. Tests use a disposable database and synthetic accounts.
