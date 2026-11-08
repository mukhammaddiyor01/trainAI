# Exercise Selection Readiness

Reviewed 2026-11-08. This boundary records why a sourced exercise can or cannot
enter a future workout selector. It does not prescribe a movement, establish
medical clearance, or generate a workout.

## Evidence and decision

The [U.S. Physical Activity Guidelines, second edition](https://odphp.health.gov/sites/default/files/2019-09/Physical_Activity_Guidelines_2nd_edition.pdf)
describe muscle-strengthening activity and gradual progression. Their population
guidance does not validate the technique, load, repetitions, or individual
suitability of any TrainAI catalog ID. [CDC guidance](https://www.cdc.gov/physical-activity-basics/guidelines/chronic-health-conditions-and-disabilities.html)
advises people with chronic conditions or disabilities to discuss appropriate
activity types and amounts with a qualified professional. A self-reported
limitation needing adaptation therefore needs a separate review path.

The six bundled exercise records have reviewed provenance and equipment only.
Their upstream `source_level` is not an eligibility verdict. Every current record
remains blocked from automatic selection until an exercise-specific suitability
and dosage review supplies supported sets, repetitions or hold duration, rest,
recovery, and alternatives. This is an unresolved product requirement, not a
claim that the exercise itself is unsafe.

## Fail-closed application rule

The plain service reports exact blockers for missing training preferences,
unavailable required equipment, and a missing, unsure, or adaptation-needed
movement answer. A `none_reported` answer removes only that self-report blocker;
it is not clinical clearance. Every current exercise still receives
`exercise_prescription_unreviewed`. The selector rejects unknown IDs and any
record with blockers. No source level, equipment access, schedule pair, or
general guideline silently supplies the missing review.

This service is offline and contains no account data. Future private API or plan
storage must read only the authenticated owner's saved inputs and retain the
existing strict request/response, rate, and ownership controls.
