# Weekly Weight Observation Review

Decision recorded 2026-11-11. This read-only review summarizes explicit daily
weight entries. It is not a trend model, adherence score, diagnosis, calorie
recommendation, or plan revision.

The current date comes from the saved profile IANA zone. Weeks begin Monday.
Show the current week and four prior weeks, newest first. Read by date bounds,
at most 35 entries; the 30-entry log list could omit the fifth week. A date
remains as saved after a profile-zone change. Current-week data ends today.

For each week, show observed-date count. Missing days remain unknown. With at
least two distinct dates, show first and last weights and their signed observed
change. One entry has no comparison; an empty week has no weight value. A change
is not a trend, predicted rate, or reason to change a goal, target, or plan.
Workout and meal adherence cannot be inferred from weight observations.

Implement plain calculation, owner-scoped bounded read, guarded API, and private
view as separate verified increments.

## Implemented flow

`GET /api/weight-review` derives the owner from the session, rejects query
parameters, and returns exactly five bounded, allowlisted weekly summaries.
The storage read uses the saved profile zone and explicit local-date bounds in
one transaction. `/weight-review` requires sign-in and a saved profile, shows
truthful empty and single-observation states, and links back to the daily log.
There is no review write, plan proposal, or new table. Synthetic two-user,
calendar-boundary, 35-date, API, and page checks passed in disposable PostgreSQL.
