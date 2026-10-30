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
