# Adult Energy Estimation

Method review: 2026-11-02. Selected method: dri-2023-adult-eer-v1.
Private preference storage, strict APIs, and an explicit browser form now connect
the reviewed service. Estimates do not create gain/loss calorie targets or plans.

## Reviewed sources and decision

Use the 2023 DRI adult Estimated Energy Requirement equations (Table 5-16) for
ages 19+. Their output is kcal/day, based on age in years, height in cm, weight
in kg, sex-specific coefficients, and a whole-day activity category. EER is an
estimate of energy balance, not an individual measurement or gain/loss prescription.

- [National Academies, 2023, chapter 5, Table 5-16](https://www.nationalacademies.org/read/26818/chapter/7)
- [Health Canada adult equations and activity definitions](https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/equations-estimate-energy-requirement.html)
- [National Academies summary: calculation followed by weight monitoring](https://www.nationalacademies.org/read/26818/chapter/2)

For comparison, [Mifflin–St Jeor](https://pubmed.ncbi.nlm.nih.gov/2305711/)
estimates resting expenditure; using it for daily expenditure would require a
separately justified activity model. The selected DRI equations estimate daily
energy directly. No resting-energy multiplier or extra exercise calories are added.

The National Academies describes prediction uncertainty and subsequent monitoring.
An equation estimate alone must not activate or revise a plan. The equations
are population references; application input limits do not establish individual
suitability or accuracy. No guaranteed accuracy or completion date is claimed.

## Coefficients and units

EER = constant + age coefficient × age + height coefficient × height
+ weight coefficient × weight. These are the eight adult rows, cross-checked
between Table 5-16 and Health Canada's adult table:

| Equation sex | Activity category | Constant | Age | Height | Weight |
| --- | --- | ---: | ---: | ---: | ---: |
| male | inactive | 753.07 | -10.83 | 6.50 | 14.10 |
| male | low_active | 581.47 | -10.83 | 8.30 | 14.94 |
| male | active | 1004.82 | -10.83 | 6.52 | 15.91 |
| male | very_active | -517.88 | -10.83 | 15.61 | 19.11 |
| female | inactive | 584.90 | -7.01 | 5.72 | 11.71 |
| female | low_active | 575.77 | -7.01 | 6.60 | 12.14 |
| female | active | 710.25 | -7.01 | 6.54 | 12.34 |
| female | very_active | 511.83 | -7.01 | 9.07 | 12.56 |

Adult PAL ranges are inactive [1.00,1.53), low_active [1.53,1.68), active
[1.68,1.85), very_active [1.85,2.50). These identify source categories; the app
will not infer a PAL number from a job, a gym schedule, or step count. Existing
training activity describes time outside planned workouts and is not this input.

## Explicit inputs and application boundaries

New calculation preferences require three explicit fields with no defaults:

- equation_sex: male, female, or unsure. This selects source coefficients, not
  gender identity. Never infer it from a name, account, or other preferences.
- activity_category: inactive, low_active, active, very_active, or unsure. It
  represents whole-day activity, including exercise, and needs separate selection.
- context: general_adult, pregnant, breastfeeding, clinical, or unsure. This is
  a self-reported scope answer, not diagnosis or medical clearance. It need not
  reveal a condition; clinical is sufficient to mark needs outside this MVP.

Unsure choices can be represented honestly but cannot produce an estimate.
Pregnancy (including first trimester), breastfeeding, and clinical contexts are
excluded by application scope, not a claim the source lacks relevant equations.
An age-18 profile remains valid onboarding data but cannot use this adult method;
no adolescent equation is silently substituted. Age 19–120 and the existing
height/weight bounds are application limits; no new clinical reference range is
asserted. Only the current profile weight is used, never a goal baseline/target.

Revalidate service values at calculation time. Reject missing/invalid inputs and
nonpositive/nonfinite results rather than inventing a default or clamping calories.
Return a versioned immutable estimate without premature rounding. No goal offset,
macro target, household portion conversion, food selection, storage, or plan is
part of this calculation. Future private collection must use existing ownership,
strict schema, request/response limits, and origin/session guards. No existing
profile is backfilled with invented answers.


## Initial service milestone — 2026-11-02

backend/services/energy_preferences.py validates all three choices and returns
immutable values. Saving uncertainty is not the same as calculation eligibility.
backend/services/energy_estimation.py revalidates ProfileDetails and preferences,
checks age/context/uncertainty, and returns AdultEnergyEstimate with kcal/day,
method version, and the two selected equation keys. Missing or forged dataclass
values cannot bypass validation. No private inputs or results are logged or sent.

Four preference-rule tests cover all 75 valid choice combinations, strict/missing
inputs, exact labels, redaction, and immutable unknowns. Eight estimate tests cover
all eight independent numerical fixtures, fractional precision, 67 excluded or
uncertain combinations, age 18/19, malformed service values, current weight,
time-zone independence, nonpositive output, immutable results, and offline operation.
All 143 application checks passed, none skipped, in disposable PostgreSQL with
migration round trips and cluster cleanup. pip check and offline catalogs passed.

No schema/dependency/HTTP/UI change was introduced; no real database was accessed.
Browser testing and the historical advisory audit were not repeated. Next: store
private calculation preferences per profile, add the guarded strict API, and then
an explicit explanatory input form. Keep these as separate verified commits.
The current method is backend-only; no existing user has been assigned answers
or a calorie target.


## Private collection and estimate flow — 2026-11-02

Migration 0006 adds one energy_preferences row per profile, with exact non-null
SQL choices, a cascading owner foreign key, and no defaults or backfill. Atomic
upserts replace all three fields. Reads and writes return plain validated values;
no calorie result is stored. Concurrent updates keep one complete selection.

GET/PUT /api/energy-preferences expose exactly equation_sex, activity_category,
and context. PUT requires a saved profile, shared session/Origin guards, strict
schemas, and bounded JSON up to 2048 bytes. Missing saved preferences return 404;
missing-profile writes return 409. Unknown owner/role/profile/calculated fields,
coercion, ambiguous JSON, and invalid choices are rejected without input echoes.
Existing rate, time, response-size, and browser security controls apply.

GET /api/energy-estimate loads only the authenticated owner's profile/preferences
through one joined SQL statement. It recomputes from current weight, revalidates
scope, and returns only energy_kcal_per_day, method_version, equation_sex, and
activity_category. Missing inputs return 404; uncertainty/age/context/nonpositive
exclusions return 409. Goal baseline/target and query values do not supply inputs.

/energy-preferences requires sign-in and a saved basic profile. The form has
three explicit selects, unsure choices, context and whole-day activity guidance,
a source link, and a truthful empty/unavailable state. Local JavaScript PUT uses
a 15-second timeout, disabled fields during save, and textContent feedback. Edits
hide the old estimate and saved notice; successful saves reload stored values.
Native method POST prevents values entering query strings; JavaScript is required.
The display rounds kcal/day to a whole number; service/API values remain unrounded.
No input/result enters browser storage or application logs. Account and food
pages link to energy preferences. No other preference is inferred or overwritten.

Four storage, five preference API, four estimate API, and two page checks passed
independently. The full disposable PostgreSQL suite passed 158 tests, none skipped,
with migration round trips. Synthetic browser checks verified empty/profile-first,
unsure and clinical exclusions, eligible save/reload, stale-result clearing,
category guidance, desktop/mobile layout, and logout protection. No horizontal
overflow or console warning/error was observed; viewport overrides were reset and
the owned test cluster/data removed. pip check and offline catalog checks passed.

After revision/table-conflict checks, the configured database was explicitly
upgraded 0005 to 0006. Existing records were preserved; no synthetic data was added.
The capped loopback launcher was started on port 8000. Anonymous page/API guards,
local script delivery, no-store, and absent Server headers passed live checks.
No dependency changes or advisory audit were performed. Gain/loss policies,
exercise prescriptions, food composition eligibility, and plans remain separate.


## Explicit adjustment previews — 2026-11-04

The [calorie preview service/API](calorie-preview.md) now builds on this estimate
with an explicitly requested adjustment and separate authored scope limits.
Profile, energy choices, and saved goal are read in one owner-scoped snapshot.
The maintenance endpoint and form retain their existing contracts; no preview
request changes them or persists/activates a target. Preview UI and plan approval
remain separate future increments.
