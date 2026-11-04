# Bounded Calorie Adjustment Preview

Reviewed 2026-11-04. Policy: manual-adjustment-preview-2026-11-04-v1.
This is an explicit-request arithmetic preview for future plan proposals. It
creates no saved target or plan. A protected API is available; a browser form
remains a separate next increment.

## Evidence and limits of the evidence

[NICE NG246, 1.16](https://www.nice.org.uk/guidance/ng246/chapter/Physical-activity-and-diet)
emphasises individualised dietary approaches, support/follow-up, and clinical
supervision for restricted low-energy diets. The indexed official text was
available during review; directly opening the page returned 403. No paywall or
access control was bypassed. It does not establish one automatic offset for all
TrainAI users. [NHS gain guidance](https://www.nhs.uk/live-well/healthy-weight/managing-your-weight/healthy-ways-to-gain-weight/)
describes gradual gain and circumstances requiring assessment; its example
calorie increases are not universal defaults or muscle-gain guarantees.

[NIDDK's planner scope](https://www.niddk.nih.gov/health-information/weight-management/body-weight-planner)
excludes pregnancy/breastfeeding and is a different model. TrainAI does not
implement its forecasts. The [existing DRI source review](energy-estimation.md)
remains the maintenance-energy method; it is not a weight-change model.
[NHS malnutrition information](https://www.nhs.uk/conditions/malnutrition/)
identifies low BMI as a risk indicator. BMI is an imperfect screening measure,
not a diagnosis or medical clearance.

## Authored application policy, not clinical recommendations

The following experimental bounds are TrainAI product decisions. None of the
sources validates these exact numbers, establishes nutritional adequacy inside
them, or guarantees an outcome. They narrow the supported preview only:

- Require all existing DRI input/context checks and a valid saved goal.
- Require an explicitly supplied whole-number adjustment magnitude, with no
  default: 1–250 kcal/day for gain/loss, exactly 0 for maintenance. Reject negative
  values, booleans, strings, fractional numbers, and absent values.
- The magnitude must also be at most 10 percent of the current maintenance
  estimate. Reject excessive requests; never clamp or silently substitute one.
- The resulting preview must be at least 1500 kcal/day. This is an application
  refusal floor, not a statement that 1500 kcal meets any individual's needs.
- Current and target BMI must be at least 18.5 and below 40 for this initial
  preview scope. These screening bounds do not establish fitness for treatment.
  Basic profiles/goals and maintenance estimates keep their existing scope;
  do not rewrite them when this narrower preview is unavailable.
- A gain/loss target must still be on the stated side of current profile weight.
  If current weight reaches or crosses it, require goal review; do not infer
  completion, reverse the offset, or change the stored starting-weight snapshot.

Use current weight to recompute maintenance energy. Validate goal consistency
against its original starting snapshot, not an invented replacement baseline.
Apply the requested magnitude positively for gain and negatively for loss;
maintenance uses the unchanged current estimate. Do not derive calories or a
completion date from kilograms remaining, or convert gain into measured muscle.

Return immutable current maintenance, signed adjustment, preview kcal/day, goal
direction, energy-method version, policy version, and explicit preview status.
Retain calculation precision; presentation rounding belongs to a later UI.
No values are logged, sent externally, persisted, approved, or converted to food
selection. Approval/versioning and a guarded user-facing preview remain separate
future work, with one owner-scoped snapshot of all inputs required at that stage.


## Protected preview API

POST /api/calorie-preview accepts exactly adjustment_kcal through the shared
session/exact-Origin guards and a strict 2048-byte JSON contract. There is no
default. The owner, direction, profile, energy values, versions, and result status
cannot be supplied in the body. The server loads profile, energy preferences,
and goal with one owner-scoped joined SQL statement and passes only plain values
to the service. Missing inputs return 404; scope/goal review returns 409; invalid
or excessive requests return 422. Existing time/rate/response limits apply.

The allowlisted response contains seven preview fields. No target, goal, profile,
preference, or plan is written. Query owner/calculation fields do not supply
inputs. Repeated requests recompute from current saved inputs, without caching a
previous eligible result. Five targeted API checks passed in disposable PostgreSQL,
covering Origin/session guards, two-owner isolation, spoofed fields, revoked access,
strict/missing/oversized/ambiguous JSON, response allowlisting, input preservation,
and current-weight/context changes. No schema or dependency was introduced.
