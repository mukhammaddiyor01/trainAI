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
