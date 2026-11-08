# Web Foundation Verification

Date: 2026-10-29.

Story: a visitor opens the local page, FastAPI renders the Jinja2 template, and the
browser loads local CSS and displays the actual development status.

## Automated checks

`python -m pip check`: no broken requirements found.

`python -m unittest discover -s tests -v`: seven tests passed.

Coverage includes page rendering and honest feature availability, web-only health,
CSS delivery, private-file/traversal boundaries, unexpected hosts, browser policies
on success/error responses, and rejection of private profile writes.

## Browser checks

The local Uvicorn server started successfully on 127.0.0.1:8000. The page and CSS
loaded in the in-app browser. Desktop and mobile breakpoint overrides were used;
both layouts were inspected. Rendered document width did not exceed viewport width
at the inspected sizes. The effective browser viewport can differ from the
requested override due to browser zoom.

Project status navigation, the roadmap disclosure, and Back to top worked. The
disclosure exposed its expanded content. The browser console returned no warnings
or errors. Temporary viewport overrides were reset after verification.

## Limits

There is no database or model boundary in this milestone. Authentication, private
data isolation, fitness calculations, inference, camera accuracy, and the complete
fitness product workflow have not been tested because they are not implemented.

## Account-access increment

All 29 tests passed through scripts/test_postgres.py against a fresh temporary
PostgreSQL cluster. This includes account normalization, password hashing, token
rotation/expiry/revocation, schema parity, transaction rollback, HTTP request
boundaries, same-origin enforcement, and two-user session isolation. The runner
also verified downgrade/upgrade exclusively inside its owned disposable cluster.

Browser registration → sign-in → account page → logout was verified on the
separate disposable server. After logout, /account redirected to /login. Invalid
password feedback appeared without reflecting credentials, and the password field
was cleared. Desktop and mobile layouts were inspected with no horizontal
overflow at the checked sizes. No unexpected JavaScript errors were observed.

The real database connection and explicit 0001 migration were checked separately;
no synthetic test accounts were written there. The temporary browser cluster was
stopped and removed. Profiles, fitness calculations, AI, and camera behavior remain
unimplemented and untested.

## Security and basic-profile increment

All 53 tests passed in the isolated PostgreSQL runner with no skipped checks.
Added coverage includes strict schema and response allowlisting, ambiguous JSON,
mass assignment, identity guards, normalized login throttling, bounded limiter
state, API rate limits, slow/chunked requests, header/URL limits, proxy spoofing,
partial-response leak prevention, safe response failures, unique test-cookie
namespaces, active SQL timeouts, and private profile read/write isolation.

Browser registration → sign-in → basic profile → save → reload → invalid time-zone
update → reload → logout was verified with synthetic data. Saved values persisted;
the invalid update preserved the old profile. Desktop and mobile layouts were
inspected with no horizontal overflow at the checked sizes. Test data and clusters
were removed. The real database received only the reviewed additive profile
migration; no synthetic profiles were written to it.

PyPA pip-audit 2.10.1 checked all 29 pinned dependencies using the PyPI advisory
service on 2026-10-29, exiting 0 with no known vulnerabilities. The full public
package report is saved as docs/dependency-audit.json. No code, .env, or private
profile data was sent for the audit. The audit tool used a separate temporary
virtual environment, not the application's runtime environment.

## Goal increment and selected password policy — 2026-10-30

Read all 10 existing project Markdown files before implementation. Preserved the
local password edit until the user explicitly selected an 8-character minimum.
Independent goal-rule, storage, API, and page tests were run with explicit patterns.
All 67 tests passed against exact committed snapshot 15b413e while excluding the
then-unresolved user edit. After aligning service/schema/rendered forms to the
selected policy and adding a minimum-length login check, all 68 working-tree tests
passed with no skips in disposable PostgreSQL. Migration round trips also passed.

Goal coverage includes missing-profile rejection, owner isolation, forged owner
and starting-weight fields, invalid target rollback, stable snapshots across
profile edits, concurrent identical saves, and PostgreSQL shape constraints.

Browser checks used only synthetic records in a disposable cluster: profile-first
redirect, profile save, invalid gain target rejection, valid goal save/reload,
profile weight changes with preserved goal baseline, identical goal retries,
maintenance without a target field, stale-success-message clearing, mobile layout,
and logout. Temporary clusters were removed. The real database was upgraded
explicitly to 0003 after conflict/revision checks; existing data was preserved.
No new dependencies or model downloads were introduced; the 2026-10-29 advisory
audit is historical and was not rerun for these code-only changes.


## Training-preference milestone — 2026-10-31

Story: a signed-in user opens Training preferences, saves experience, activity,
equipment, available days, and session time through the guarded API, then reloads
stored private selections from PostgreSQL.

| Boundary | Evidence |
| --- | --- |
| UI entry and guards | Account/goal links; anonymous login redirect; profile-first redirect |
| Client to API | Browser form saved bodyweight preferences, then equipment/duration changes |
| API to data | Owner-keyed upserts; two-user and concurrent-retry PostgreSQL tests |
| Data to response | Five-field allowlisted response; invalid updates retain prior values |
| Response to UI | Saved selections rendered after navigation and explicit reload |

Four rule tests, four storage tests, five API tests, and two page tests passed as
separate targeted increments. The complete isolated PostgreSQL suite then passed
83 tests, none skipped, including migration round trips. `pip check` passed.
Browser verification also covered no selected weekdays, stale-success clearing,
logout, and desktop/mobile layouts. At effective viewport widths 1163 and 354 CSS
pixels, no element extended beyond the viewport; no console warnings/errors were
reported. Overrides were reset; synthetic data and the owned cluster were removed.

The configured database was explicitly upgraded from 0003 to 0004 after conflict
checks. The current loopback runtime returned /login 200, /training-preferences
303 to login without a cookie, /api/training-preferences 401, and the new local
script 200; checked responses used no-store and omitted Server headers.
No synthetic records were written to the configured database. Dependencies were
unchanged; the 2026-10-29 advisory audit was not rerun. Food preferences, calculations,
generated plans, AI, and camera work remain unimplemented.


## Food-preference milestone — 2026-10-31

Story: a signed-in user records diet, explicit allergy information, spending style,
preparation time, and local meal times; the guarded API persists one private row
and the page reloads canonical stored values.

Five plain-rule tests, four storage tests, five API tests, and two page tests
passed. The first page run found a conditional Jinja expression error; it was
corrected before verification continued. The complete disposable PostgreSQL suite
then passed 99 tests, none skipped, including migration downgrade/upgrade.

Browser → API → PostgreSQL → rendered page was checked with synthetic data:
profile-first redirect; unsure status; listed allergy names; duplicate rejection;
explicit clearing to none_reported; meal-time sorting, adding/removing within 1–8
entries; zero preparation; reload persistence; stale-success clearing; and logout.
Reported-name escaping was checked by the page test. At inspected 1280 and 390
viewports there was no horizontal overflow; browser console returned no warnings
or errors. Overrides were reset; the owned test cluster and synthetic data were
removed. `pip check` passed; dependencies did not change and the 2026-10-29
advisory snapshot was not rerun.

The configured database was explicitly upgraded 0004 → 0005 after conflict checks.
Existing tables were not modified. The restarted loopback runtime returned /login
200, anonymous /food-preferences 303 to /login, /api/food-preferences 401, and the
local food script 200. Checked responses used no-store and omitted Server headers.
No synthetic profiles or food preferences were written to the configured database.
Food safety assessment, monetary pricing, calorie targets, generated plans, and
AI remain outside this implemented milestone.


## Catalog seed milestone — 2026-10-31

Read all 13 existing project Markdown documents before implementation. Reviewed
and pinned six exercise records to upstream commit
f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5 with its Unlicense notice. Reviewed four
official USDA SR Legacy nutrient records with CC0 provenance, source IDs, per-100-g
edible basis, raw/cooked identity, retained API responses, and SHA-256 hashes.

Four exercise tests, six food tests, five use-rule tests, and two offline-check
tests passed. Coverage includes incomplete upstream equipment labels, source
metadata/value/unit parity, missing nutrients, corrupt evidence, ambiguous JSON,
unknown IDs, unsupported fields, strict portion mass, and blocked food selection.
The offline check passed with sockets denied and an unusable DATABASE_URL. It
reports six exercise/four nutrient records and unavailable food selection.

Live source-link verification found USDA website detail paths returned 404; links
were corrected to the documented API resources that supplied the records. Runtime
loads remain offline. USDA public-demo limits apply only to explicit source access.

The complete disposable PostgreSQL runner passed 116 tests, none skipped, including
migration round trips. `pip check` passed. No schema/dependency/UI/HTTP changes were
introduced, no browser check was repeated, and the configured database was not used.
The historical advisory audit was not rerun. These are metadata/nutrient seeds,
not approved food-allergen composition, clinical safety review, exercise dosage,
daily calorie targets, or generated workout/nutrition plans.

Final source-audit refinement additionally rejects prepared nutrient/name drift
against retained USDA values even when the source hash remains unchanged. Its
regression passed, then the complete suite was rerun and passed all 116 checks.


## Allergy-name readiness milestone — 2026-11-02

Read all 14 existing Markdown files before implementation. Started on clean,
synchronized develop at dd69dc4. Reviewed FDA Edition 5 (January 2025) and the
current FDA FAQ for the bounded terminology scope, while retaining unresolved
food-composition evidence. No private data was sent during source review.

Five resolver tests cover the exact nine-group/fifteen-name subset, shared saved
normalization, immutable results, equivalent alias collapse, malformed/bounded
input, ambiguous/species/translated names, and registry collisions. Two new
readiness tests confirm recognized names retain composition/ingredient blockers
and partial matches never drop unknown restrictions; all seven use tests passed.
Three operator tests verify offline operation with sockets denied and unusable
DATABASE_URL, accurate public counts/version, pending reviews, and safe failure.
Inspection of the four retained USDA responses found no ingredient declarations
or root-level allergen fields; all four foods remain blocked from selection.

The complete isolated PostgreSQL runner passed 124 tests, none skipped, including
migration round trips. `pip check` passed. No dependency/schema/UI/HTTP changes
were introduced and the configured database was not used. Browser verification
and the historical advisory audit were not repeated. A read-only startup check
found no port-8000 listener; this milestone did not start/stop servers. This is
name resolution/readiness plumbing, not clinical assessment or meal planning.


## Explicit portion totals — 2026-11-02

Read all 15 project-owned Markdown documents and confirmed clean develop at
f5b59ce. Rechecked the current official USDA data-type/API documentation and
retained composition evidence. The four SR Legacy sources do not provide the
needed product composition evidence; their nutrition_only state is unchanged.

Seven new service checks cover multi-food/source-based totals, repeated portions,
raw/cooked separation, split-mass consistency, missing-vs-zero nutrients,
malformed/oversized collections, invalid masses, unknown-ID rejection without
skipping rows, immutable/detached results, and offline operation with unchanged
eligibility blockers. The existing seven use-rule and six food-catalog checks
also passed independently (20 targeted checks total).

All 131 tests passed in disposable PostgreSQL, none skipped, with migration
round trips. The owned temporary cluster was removed. pip check and the explicit
offline catalog check passed. No dependency/schema/API/UI changes were introduced;
no runtime was started/stopped and no browser check or historical advisory audit
was repeated. The configured database was not contacted. This increment totals
specified portions; it does not record a meal, determine personal energy needs,
recommend foods, or create a plan.


## Adult energy-method services — 2026-11-02

Read all 15 existing project-owned Markdown documents and confirmed clean develop
at da04b5a. Reviewed National Academies 2023 Table 5-16, its summary, and the
Health Canada adult table and whole-day PAL definitions before coding. The source
and scope decision was committed separately, followed by input and calculation
service commits. New method documentation brings the inventory to 16 files.

Four input-rule tests passed, then eight calculation tests passed independently.
These include all eight numerical reference cases and 67 valid-but-ineligible
choice combinations, exact/strict input types, unknowns, age boundaries, forged
service values, decimal precision, changed current profile weight, time-zone
independence, nonpositive-result rejection, immutable outputs, and offline use.

The complete disposable PostgreSQL suite passed 143 tests, none skipped, including
migration downgrade/upgrade; its owned cluster was removed. pip check and offline
catalog verification passed. No dependencies, schema, API, UI, or runtime launcher
changed. The configured database was not contacted. No browser check or historical
advisory audit was repeated. Energy preference persistence/collection and a
user-facing estimate are still unimplemented; no calorie target or plan is active.


## Energy onboarding end to end — 2026-11-02

Read all 16 project Markdown files; started on clean develop at ca710a4. Storage,
preference API, estimate API, and UI were each independently tested and committed.

| Boundary | Verified behavior |
| --- | --- |
| Browser to API | Explicit selections saved with PUT; profile-first redirect and local scripts |
| API to database | Owner-scoped complete upsert, strict choices, missing-profile rejection |
| Database to estimate | One joined SQL snapshot, current weight, no goal-baseline substitution |
| Response to browser | Stored choices and eligible estimate reload; unsure/clinical state has no calories |
| Security | Owner/role/profile/result injection rejected, revoked access, bounded/redacted JSON, allowlisted response |

Four storage, five preference API, four estimate API, and two page tests passed
as separate targeted checks. The full isolated PostgreSQL suite passed 158 tests,
none skipped, including migration downgrade/upgrade and model parity. pip check
and offline catalog validation passed; dependencies were unchanged.

Synthetic browser flow covered registration/sign-in, profile-first redirect,
profile save, initially blank selects, unsure save, eligible estimate save/reload,
clinical exclusion, stale success/result clearing on edits, expanded activity
guidance, and logout protection. Mobile/desktop checks at effective 355/1164 CSS
pixel widths (requested 390/1280) found no horizontal overflow. Console inspection
returned no warnings/errors. Overrides were reset, the test tab closed, and the
owned browser cluster and data removed. A screenshot outside the repository
contains only synthetic profile values. No capture or private fixture was committed.

Verified configured revision 0005 and no new-table conflict, then explicitly
applied additive migration 0006 and checked its four columns. Existing records
were preserved; no synthetic data was written there. Started the capped canonical
loopback launcher on port 8000. Live /login returned 200, anonymous energy page
303 to /login, both energy APIs 401, and local energy JavaScript 200. All checked
responses used no-store and omitted Server. An initial sandbox loopback probe
was denied; the same read-only check passed with authorized local network access.

The historical advisory audit was not rerun. The new output is an estimate of
maintenance energy, not a prescribed calorie target, measured expenditure,
automatically selected meal/workout, or approved plan revision.


## Calorie preview service and guarded API — 2026-11-04

Read all 16 existing Markdown files; develop was clean at cbb64c0. Reviewed
NICE/NHS/NIDDK sources and documented experimental application bounds before
implementation. Direct NICE access returned 403; official indexed text was
available, and no access controls were bypassed. Policy review, service, and API
were committed independently; the new policy document brings the inventory to 17.

Eight service checks cover gain/loss/maintenance, explicit strict magnitude,
absolute/relative limits, floor and BMI boundaries, current vs starting weights,
reached/crossed goals, uncertain/excluded contexts, malformed inputs, immutability,
precision, and offline operation. Five API checks passed in disposable PostgreSQL:
Origin/session guards, complete prerequisites, seven-field response allowlisting,
no saved-input changes, owner/result injection, two-owner isolation, revoked
access, oversized/ambiguous JSON, redaction, and rejection of stale eligibility.

The full suite passed 171 tests, none skipped, including disposable migration
round trips and cluster cleanup. pip check and offline catalog verification passed.
No dependencies or schema changed; the configured database was not contacted.
No private real records were read or written. Expected revision remains 0006.

Started the canonical capped local server on 127.0.0.1:8000 after confirming no
listener. Live login returned 200, preview without Origin 403, and same-Origin
anonymous preview 401, all with no-store and no Server header. No UI changed,
so browser checks were not repeated; the historical advisory audit was not rerun.
No calorie target or plan was stored/activated. Explanatory preview UI and
transactional approval/version history remain next increments.

## Explicit preview browser flow — 2026-11-04

Read all 17 project-owned Markdown files and started from clean synchronized
develop at dad6d1f. Added authenticated `/calorie-preview` with profile-first
redirect, honest missing-prerequisite state, blank requested adjustment, authored
limit explanations, and a temporary API result display. Only the explicit
integer magnitude is sent; no browser storage/query value or approval control
is involved. Two focused page tests passed.

A synthetic account in the owned disposable PostgreSQL browser runner saved a
profile, goal, and energy preferences. The form displayed 2,753 kcal/day from a
2,553 kcal/day rounded maintenance estimate and +200 requested adjustment;
precise service values remain unrounded. Editing hid the result; reload restored
an empty field and no result. At a requested 390 px mobile viewport, effective
document width and scroll width were both 375 px; console had no errors/warnings.
The viewport override was reset and the temporary tab, account, and cluster
removed. No real user records were entered into the test browser.

The full disposable PostgreSQL suite passed 173 tests, none skipped, with
migration round trips. pip check passed. No schema/dependency changes, configured
database access, or advisory-audit rerun occurred. Preview values remain
transient; proposal storage and transactional approval/version history are pending.

## Pending proposal storage and API — 2026-11-05

Read all 17 existing project-owned Markdown files on clean synchronized develop
at e48855d. Added the authored pending-only storage boundary, migration 0007,
owner-scoped transactional creation/read, and strict guarded create/read APIs
in separate verified commits. The new boundary document brings the Markdown
inventory to 18. Two SQL schema, three storage, and three API tests passed
independently. Checks include forged status, amount, owner and result fields,
missing/changed inputs, owner-only reads, revoked sessions, ambiguous/oversized
JSON, preserved goal/energy values, and immutable prior snapshots.

The full isolated PostgreSQL suite passed 181 tests, none skipped, including
migration round trips and owned-cluster cleanup. pip check and offline catalog
validation passed. Configured database connectivity returned a generic success;
revision was 0006 and the proposal table absent. The additive migration was
explicitly applied and revision 0007 verified. No real profile or proposal rows
were read or written, and no dependency/UI changes or browser checks occurred.
No target or plan activation, approval, or idempotent approval is implemented.
The capped loopback launcher was started on port 8000. A live anonymous POST
with the correct Origin returned 401, with no-store and no Server header.

## Pending proposal browser flow — 2026-11-05

Read all 18 project-owned Markdown files before implementation. The private
proposal review page passed two focused disposable PostgreSQL checks for owner
access, other-owner/missing 404 responses, anonymous redirect, and pending-only
copy. The preview page passed two focused checks after adding the explicit save
control. The increments were committed separately as 0ce484e and 2b6c47a.

A synthetic account in the owned disposable browser server saved a profile,
goal, and energy choices, calculated a +200 kcal/day preview, then explicitly
saved a pending proposal. The browser reached its owner-only URL and reload
retained the saved snapshot. The requested 390 px mobile viewport produced equal
375 px document and scroll widths; console warnings/errors were absent. The
viewport override was reset, and the owned tab/server/test cluster were removed.
No configured user records were used. The complete isolated suite passed 183
tests, none skipped, with migration round trips. pip check and offline catalog
verification passed. No dependency/schema or active-target change occurred.

## Owner-only proposal discovery — 2026-11-05

Read all 18 project Markdown documents before implementation. A bounded
timestamp/UUID cursor storage query, strict owner-scoped list API, and private
list page were verified and committed separately. Storage checks covered 23
owner proposals across 20/3-record pages, ordering, no overlap, foreign and
missing cursors. API checks covered an empty list, allowlisted results, another
owner's empty list, and invalid/duplicate/unexpected cursor fields. Page checks
covered anonymous redirect, owner-only pagination, and account navigation.

The disposable browser flow checked the empty list, then saved a synthetic
proposal from the preview and found it through the new list. Desktop width was
1280/1280 document/scroll pixels; requested 390 px mobile width was 390/390.
No console warnings or errors were observed. The temporary browser tab, server,
and synthetic database were removed. Full isolated PostgreSQL regression passed
187 tests, none skipped, with migration round trips. pip check and the offline
catalog check passed. No configured user data, migration, dependency, active
target, or approval changed.

## Explicit calorie target approval — 2026-11-06

Read all 18 project-owned Markdown files before implementation, starting from
clean synchronized develop at ae1d787. Reviewed and committed the approval
boundary, constrained migration 0008, active-baseline proposal snapshot,
transactional approval, guarded API, owner-only bounded history, and browser
pages as separate small commits. The strict confirmation test caught Pydantic's
coercion of `Literal[True]` from numeric 1; a strict boolean field with an exact
true validator now rejects it. A UTC normalization fix makes approval retries
return an identical timestamp representation.

The full disposable PostgreSQL runner passed 196 tests, none skipped, with
migration downgrade/upgrade and owned-cluster cleanup. Tests include concurrent
idempotent retries, stale input/baseline rejection, SQL one-active constraints,
two-owner API and page isolation, and pending/approved browser copy. An isolated
port-8001 anonymous browser visit redirected `/calorie-targets` to login; no
synthetic account was created in that manual browser check, and its tab/server/
cluster were removed. The configured database was verified at revision 0007
with no target table, then explicitly migrated to 0008. Schema metadata, not
user rows, was inspected. No AI or full plan was activated.

`pip check` and offline catalog verification passed. The updated bounded local
server started on port 8000. Live anonymous requests returned 303 to login for
the private target page and 401 for active/history APIs, with no-store and no
Server header. The server was left running for local use.

## Movement limitation collection — 2026-11-06

Read all 19 project-owned Markdown files, including AGENTS.md and the cumulative
handoff, before implementation. Started on clean synchronized develop at af2c20d.
Reviewed official WHO adult activity guidance and CDC chronic-condition and
getting-started guidance; documented why source-level exercise metadata and
population activity targets are not individual prescriptions. The boundary,
strict plain validation, migration/storage, guarded API, and private page were
verified and committed separately: 69f4a1c, 8ee183e, 5582b06, eec8bd1,
65e1ab0. The new boundary document brings the Markdown inventory to 20.

The full disposable PostgreSQL suite passed 206 tests, none skipped, including
migration downgrade/upgrade and model parity. Focused tests covered unknown
status preservation, two-user isolation, concurrent retries, SQL constraints,
profile-first access, forged/malformed/oversized API input, and private page
states. A synthetic browser account followed profile-first redirect, rejected
an empty answer, saved `needs_adaptation`, and reloaded it. The tab, server, and
cluster were removed. No real user row was entered into the browser test.

`pip check` and offline catalog verification passed. Configured schema revision
0008 and absent movement table were checked before applying additive migration
0009; revision and two new columns were verified afterward without reading user
rows. The owned loopback server was restarted. Live anonymous page/API requests
returned 303/401, the local script 200, with no-store and no Server header.
No workout, exercise dosage, medical clearance, or AI output was generated.

## Strength-day scheduling rule — 2026-11-07

Read all 20 project-owned Markdown files before implementation. Reviewed official
U.S. activity-guideline evidence and CDC adaptation guidance. Committed the
scheduling boundary and plain rule in separate increments. Three targeted checks
passed for availability, deterministic options, weekly wraparound recovery, and
invalid inputs. The full disposable PostgreSQL suite passed 209 tests, none
skipped, with migration round trips and owned-cluster cleanup. `pip check` and
offline catalogs passed. No schema, dependency, API, UI, configured database, or
server changed; browser checks were not repeated. No schedule was selected or
workout prescribed.

## Exercise selection readiness — 2026-11-08

Read all 21 project-owned Markdown files before implementation. Reviewed current
official U.S. physical activity and CDC adaptation guidance. The boundary and
plain gate were committed separately. Five focused checks passed for all six
unreviewed records, equipment completeness, missing/uncertain/adaptation answers,
unknown IDs, and forged saved values. The full disposable PostgreSQL suite passed
214 tests, none skipped, with migration round trips and owned-cluster cleanup.
`pip check` and offline catalog verification passed. No schema, dependencies,
API, UI, configured database, or server changed; browser checks were not repeated.
No exercise prescription or workout was generated.
