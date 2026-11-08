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

## Bodyweight squat source-mapping review — 2026-11-08

The [ACSM 2026 resistance-training update](https://acsm.org/resistance-training-guidelines-update-2026/)
summarizes evidence for healthy adults, supports bodyweight training, and emphasizes
individual goals and safety. It does not identify a TrainAI catalog exercise or
provide a complete prescription for its technique, rest, adaptation, and fallback.

The [NHS strength-exercise page](https://www.nhs.uk/live-well/exercise/strength-exercises/)
describes a chair-supported mini-squat with a comfortable partial bend and five
repetitions. The retained `Bodyweight_Squat` source record instead describes a
body-only squat with no chair, a different stance, and full depth when possible.
Those are distinct movement variants. Transferring the NHS mini-squat's five reps
or implied support to the current catalog ID would misstate the exercise and its
equipment requirement. The [NHS squat video page](https://www.nhs.uk/live-well/exercise/strength-and-flex-exercise-plan-how-to-videos/)
also gives general suitability cautions, not an individual clearance decision.

Decision: `exercise-bodyweight-squat` remains unreviewed for automatic selection.
No dose, rest period, adaptation, or alternative has been authored from these
sources. The other five records retain the same blocker. A future supported
mini-squat would require its own exact catalog identity and equipment review.

## Fail-closed application rule

The plain service reports exact blockers for missing training preferences,
unavailable required equipment, and a missing, unsure, or adaptation-needed
movement answer. A `none_reported` answer removes only that self-report blocker;
it is not clinical clearance. Every current exercise still receives
`exercise_prescription_unreviewed`. The selector rejects unknown IDs and any
record with blockers. No source level, equipment access, schedule pair, or
general guideline silently supplies the missing review.

The plain rule is offline and contains no account data. The private read-only
`/workout-readiness` page obtains training preferences and movement answers from
one owner-scoped database read after authentication and profile-first checks. It
shows only saved-input status, possible day-pair count, and catalog equipment
checks. It never calls a selector, chooses a day pair, or saves a workout. Future
private API or plan storage must retain strict request/response, rate, and
ownership controls.

## Verification — 2026-11-08

Five offline service checks cover all six records, complete equipment matching,
missing and uncertain answers, adaptation, unknown IDs, forged saved values, and
the refusal to select even with `none_reported`. All 214 disposable PostgreSQL
checks passed with migration round trips and owned-cluster cleanup. `pip check`
and offline catalog verification passed. No private data, schema, API, or browser
surface changed.

The later private-page increment passed 219 disposable PostgreSQL checks. Tests
cover owner isolation, profile-first access, anonymous redirect, missing/saved
inputs, and query-owner spoofing. A disposable synthetic browser session verified
the empty state after profile setup. No schema, dependency, or configured user
record changed.
