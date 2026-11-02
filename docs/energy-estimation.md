# Adult Energy Estimation

Method review: 2026-11-02. Selected method: dri-2023-adult-eer-v1.
This increment provides a plain service estimate only; persistence, API, and UI
will be separate verified steps.

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
