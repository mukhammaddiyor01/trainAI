# Strength-Day Scheduling Boundary

Reviewed 2026-11-07. This first scheduling increment finds possible pairs of
available weekdays with a recovery day between them. It does not assign a
workout, choose a pair, or claim that two sessions suit a particular user.

## Evidence and application rule

The [2018 U.S. Physical Activity Guidelines Advisory Committee report](https://odphp.health.gov/sites/default/files/2019-09/PAG_Advisory_Committee_Report.pdf)
describes muscle strengthening on two to three nonconsecutive days as a common
evidence-supported pattern. [CDC guidance for chronic conditions and disabilities](https://www.cdc.gov/physical-activity-basics/guidelines/chronic-health-conditions-and-disabilities.html)
calls for individual advice on appropriate activity types and amounts. These
population references do not validate TrainAI's six exercise records or prescribe
a session count for a saved user.

The application therefore only enumerates two-day **options** from the user's
explicitly saved Monday-first availability. Days are nonconsecutive when neither
day directly follows the other, including the Sunday-to-Monday boundary of a
repeating week. An empty result stays empty: one available day, or only adjacent
days, cannot silently become a two-day schedule. The order is deterministic;
no option is selected or stored. Session duration and experience remain saved
inputs but do not supply an intensity, exercise, set, repetition, or rest period.

The movement-limitation self-report still gates future exercise selection.
`none_reported` is not clearance. Exercise-specific suitability, dosage,
alternatives, and the actual weekly plan require separate review and rules.

## Verification — 2026-11-07

Three isolated service checks cover deterministic options, one-day and adjacent
availability, Sunday/Monday recovery, and invalid or forged saved values. All
209 disposable PostgreSQL checks passed with migration round trips and cluster
cleanup. `pip check` and offline catalog verification passed. No database schema,
API, browser page, or configured user record changed in this increment.

## Private readiness display — 2026-11-08

The authenticated `/workout-readiness` page now lists the computed pairs behind
an expandable control when saved availability contains an option. The list uses
Monday-first day names and retains the service's sorted order. Missing training
preferences and adjacent-only availability show distinct empty states. These are
spacing options, not scheduled workouts; no pair is selected or persisted.
Owner-scoped page checks cover distinct users' saved days and query-owner spoofing.
