# TrainAI — Completed Tasks and Session Handoff

Last updated: 2026-11-06 (Asia/Seoul).
The latest continuation read all 19 existing project-owned Markdown files before
implementation. The new movement boundary brings the inventory to 20.

## Current Checkpoint — Movement Limitation Collection

- Started from clean synchronized develop at af2c20d. Reviewed official WHO
  and CDC activity guidance; documented the self-report and non-prescription
  boundary in docs/movement-limitations.md (69f4a1c).
- Added strict three-state plain validation (8ee183e), owner-scoped storage and
  migration 0009 with no default/backfill (5582b06), guarded GET/PUT API
  (eec8bd1), and private English collection page (65e1ab0). Each increment
  passed focused checks before its separate commit.
- Full disposable PostgreSQL suite passed 206 tests, none skipped, with
  downgrade/upgrade and model parity. `pip check` and offline catalogs passed.
  Synthetic browser flow verified profile-first redirect, blank-answer rejection,
  needs-adaptation save, and reload. Owned test assets were removed.
- Configured database revision 0008 and absent table were checked; additive
  migration 0009 was applied and its two columns verified using schema metadata.
  No real user rows or secrets were inspected. The bounded server was restarted
  on port 8000; live anonymous page/API guards and local asset passed.
- Next: review and implement exercise-specific eligibility and dosage rules
  before any generated workout. A saved `none_reported` answer is self-report,
  not clinical clearance. `unsure`, missing, and `needs_adaptation` must block
  automatic selection or lead to an adapted review path. Food composition
  remains insufficient for automatic meal selection.

## Current Checkpoint — Private Proposal Discovery

- Continued from clean synchronized develop at b8ba7d6 after reading all 18
  project-owned Markdown files and the frontend-design skill. Implemented
  owner-scoped, newest-first keyset pagination, 20 rows per page with a 21st
  existence check. Foreign/missing cursors fail without exposing records.
  Storage checks passed; commit 8842965.
- Added guarded `GET /api/calorie-proposals` with strict single-cursor query,
  allowlisted nested responses, and no owner/source snapshot fields. Focused
  API checks passed; commit c8f1aa6.
- Added `/calorie-proposals` with empty state, older-page navigation, and links
  from account, preview, and detail views. Owner/anonymous/cursor page checks
  passed; commit edb3c7b. Synthetic browser flow verified empty and populated
  lists, detail navigation, desktop/mobile fit, and no console warnings/errors.
- Complete disposable PostgreSQL regression: 187 tests, none skipped, with
  migration round trips. pip check and offline catalogs passed. No schema,
  dependency, configured user record, active target, or approval changed.
- Next: review the transactional approval boundary in detail before implementing
  it in separate schema, service, API, and UI increments. Preserve old proposals
  and enforce one active target/version per owner in PostgreSQL.

## Current Checkpoint — Pending Proposal Browser Flow

- Continued from clean synchronized develop at 76ed876 after reading all 18
  project-owned Markdown files and the frontend-design skill. Added a private
  `/calorie-proposals/{proposal_id}` review page, with anonymous redirect and
  identical 404 for another owner's or absent ID. Focused tests passed; committed
  separately as 0ce484e.
- Added an explicit **Save pending proposal** control after a successful preview.
  Editing clears the preview and save eligibility. Saving sends the magnitude
  only; the server revalidates and recomputes from current saved inputs. The
  result redirects to the owner-only snapshot page. Focused checks and a synthetic
  disposable browser flow passed; committed separately as 2b6c47a.
- Browser verification covered preview, save, redirect, reload, 390 px requested
  mobile viewport without horizontal overflow, and no console warnings/errors.
  The owned disposable tab, server, database, and synthetic account were removed.
  Full isolated PostgreSQL regression: 183 tests, none skipped, with migration
  round trips. pip check and offline catalog verification passed. No schema,
  dependency, configured user records, or active target changed.
- Next: a bounded private proposal list would make older drafts discoverable.
  Transactional approval, stale-input checks, one active target per owner, and
  version history are separate future increments. No approval is implemented.

## Current Checkpoint — 2026-11-05

- Continued from clean synchronized develop at e48855d after reading all 17
  existing Markdown files. Added docs/calorie-proposals.md, bringing the inventory
  to 18. The reviewed boundary, pending-only schema, transactional storage, and
  guarded create/read API were separate verified commits: 4d184d0, f7656ad,
  0b26d80, and e818b9a.
- A proposal snapshots current owner profile, goal, energy choices, unrounded
  calculation, and pinned versions. Creation locks/revalidates current rows;
  prior snapshots remain intact. SQL permits only pending status. The API accepts
  only an explicit adjustment magnitude and returns nine allowlisted fields.
- Two schema, three storage, and three API checks passed independently. Full
  isolated PostgreSQL regression: 181 tests, none skipped, with migration round
  trips. pip check and offline catalog check passed. No dependencies/UI changed.
- The configured database was at 0006 with no proposal table. Additive migration
  0007 was applied explicitly and verified; no real user records were read/written.
- Started the capped loopback server on port 8000. A live anonymous proposal
  POST with exact Origin returned 401, with privacy headers and no Server header.
- Next: explicit browser save/review of pending proposals, then separately
  transactional approval, active-plan uniqueness, and version history. No active
  calorie target or plan exists yet.

## Previous Preview UI Checkpoint — 2026-11-04

- Continued from clean synchronized develop at dad6d1f after reading all 17
  project-owned Markdown files. Added `/calorie-preview` as an authenticated,
  explanatory form for the existing API. The amount is blank by default; no
  browser storage, query value, target write, or plan approval is involved.
- Page guards and prerequisite states passed two focused checks. A synthetic
  disposable browser flow verified profile-first redirect, goal/energy collection,
  +200 kcal preview, edit-time stale clearing, reload disappearance, and mobile
  width without overflow or console errors. The test cluster/account were removed.
- The full isolated PostgreSQL suite passed 173 tests with no skips and migration
  round trips. pip check passed. No dependency/schema change or configured user
  database access was made. UI increment: d7f70f6.
- Next: review proposal persistence and transactional approval/version history as
  separate small increments. Do not activate a target from a transient preview.

- Resumed from clean, synchronized develop at cbb64c0 after reading all 16 Markdown
  files. New docs/calorie-preview.md brings the inventory to 17.
- Reviewed calorie-preview evidence and authored experimental bounds, then added
  explicit-request preview arithmetic and a protected single-field POST API.
  No universal offset, nutritional adequacy, outcome, or approval is inferred.
- Service requires revalidated current profile/energy choices and original goal
  semantics. The API reads all three inputs in one owner-scoped SQL snapshot,
  retains seven allowlisted preview fields, and writes no target, goal, or plan.
- Latest implementation: 589bb99, after policy review 4d50a97 and service b76ecfa.
  Development remains on develop; master remains at a8ddfd9.
- Previous API result: 171 complete isolated PostgreSQL tests passed, none skipped;
  eight service and five API checks passed independently. Migration round trips,
  pip check, and offline catalogs passed. No schema/dependency changes were made.
- Expected database revision remains 0006; configured database/private records
  were not accessed. Browser checks and the historical advisory audit were not
  repeated because no UI/dependencies changed.
- No listeners were observed on 8000/8001 at startup. The canonical bounded
  launcher is now running on 127.0.0.1:8000. Live login returned 200; preview POST
  without Origin 403 and anonymous same-Origin POST 401, with privacy headers.
- The explanatory preview UI is complete. Separately reviewed proposal
  persistence and transactional approval/version history remain before activation.
  Exercise prescription rules/limitations and food composition evidence remain
  prerequisites for automatic workout/meal plans.

## Previous Session Handoff — 2026-10-31

Next planned continuation: 2026-11-01 (Asia/Seoul), when the user resumes work.
Before starting the next feature, discover and read every project-owned Markdown
file, including new files added after this checkpoint. Follow the inventory and
startup rules below and in AGENTS.md; then inspect Git status and user changes.

- Completed: authenticated multi-user accounts, private basic profiles, stable
  weight goals, training preferences, food preferences, and custom meal times.
- Security: shared session/origin guards, strict input/output contracts,
  owner-scoped persistence, bounded requests/responses, and rate/resource limits.
  Local login remains active; OAuth is deferred by the user's choice.
- Catalogs: 6 pinned exercise metadata records and 4 USDA nutrient records,
  source/license evidence, complete equipment filtering, exact-ID lookup,
  gram-based scaling, and explicit offline evidence verification.
- Latest verification: 116 complete isolated PostgreSQL tests passed, none skipped;
  17 are catalog checks. Migration revision remains 0005. The dependency advisory
  audit remains the historical 2026-10-29 snapshot.
- Git checkpoint: implementation d49579e, verified catalog documentation fc89ac6;
  both were pushed to origin/develop. The working tree was clean before this
  documentation-only handoff. Master remains at a8ddfd9.
- Next increment: review food ingredient/diet/allergen composition evidence and
  bounded allergy-name mapping. Keep current nutrient-only food records blocked
  from automatic selection. Review missing calculation inputs and methods before
  daily targets, and prescription rules/limitations before workout generation.
- This handoff changes documentation only; application tests were not rerun.
  No automatic task or scheduled continuation was created. Runtime availability
  must be checked again when work resumes.

## Read Before Continuing

Before editing code in any resumed session, read AGENTS.md, this file, README.md,
and every project-owned Markdown file under the repository, including new files
added later. Exclude .git, .venv, caches, and third-party dependency directories.
Discover the current Markdown inventory rather than relying only on this list:

```bash
rg --files --hidden -g '*.md' -g '!.git/**' -g '!.venv/**' -g '!.cache/**'
```

Current documentation:
- [Development rules](AGENTS.md)
- [Setup and current features](README.md)
- [Architecture](docs/architecture.md)
- [Environment and pinned versions](docs/environment.md)
- [Database and migrations](docs/database.md)
- [Authentication](docs/authentication.md)
- [Basic profiles](docs/profiles.md)
- [Weight goals](docs/goals.md)
- [Training preferences](docs/training-preferences.md)
- [Food preferences](docs/food-preferences.md)
- [Catalog seeds](docs/catalogs.md)
- [Allergy-name resolution](docs/allergen-names.md)
- [Adult energy estimation](docs/energy-estimation.md)
- [Calorie preview scope](docs/calorie-preview.md)
- [Pending calorie proposals](docs/calorie-proposals.md)
- [Movement limitation collection](docs/movement-limitations.md)
- [Security boundaries](docs/security.md)
- [Verification history](docs/verification.md)

AGENTS.md and this handoff describe the latest agreed state. Some documents retain
earlier milestone observations: the 7-test and 29-test results are historical;
the latest complete working-tree suite passed 206 tests on 2026-11-06. If documents disagree, inspect Git
history and current code before proceeding. Do not silently assume which is right.

## Confirmed Working State

The application supports account registration, sign-in/sign-out, private session
identity, and a basic private profile containing age, height, weight, and IANA time
zone, gain/loss/maintenance weight goals, and private training preferences.
Private food preferences and custom local meal schedules are implemented.
Six sourced exercise metadata records and four USDA nutrient seeds are implemented.
Bounded exact allergy-name resolution and explicit unresolved-name blockers are
implemented. Explicit multi-portion nutrient totals and reviewed adult energy
input/calculation services are connected to private energy preference storage,
strict APIs, and explicit browser onboarding. Bounded explicit-request calorie
previews are available in a plain service, guarded API, and temporary browser UI.
Pending calorie proposals are saved through a guarded API and explicit browser
action, then found in a private paged list and reviewed at a saved URL; product composition
evidence and plans remain pending. Explicitly approved calorie targets and a
private movement limitation self-report are now available.

| Area | Completed behavior |
| --- | --- |
| Foundation | FastAPI composition, Jinja2 pages, local HTML/CSS/JavaScript, responsive English UI, web-only health endpoint |
| Persistence | Explicit PostgreSQL configuration, SQLAlchemy transactions, connection check, reviewed Alembic migrations, no SQLite fallback or startup schema creation |
| Registration | Canonical unique usernames, input rules, salted Argon2id password hashes, generic failures without input/credential exposure |
| Sessions | Random 32-byte tokens, SHA-256 digests in storage, 24-hour expiry, login rotation, logout revocation, HttpOnly/host-only/SameSite cookies |
| Guards | Shared same-origin write checks and server-derived account identity; browser user_id, role, or forged Bearer values do not establish identity |
| Validation | Strict Pydantic request/response contracts, unknown-field rejection, no coercion, bounded UTF-8 JSON, duplicate-key/non-finite/compressed-body rejection |
| Allergy-name resolution | Nine reviewed groups/15 exact English terms, shared normalization, immutable results, preserved unknowns, unchanged ingredient/composition blockers, offline checks |
| Adult energy onboarding | Versioned DRI 2023 estimate from one owner-scoped snapshot; explicit stored choices, strict guarded APIs, responsive form, uncertainty/scope checks, no saved calorie target |
| Calorie preview | Explicit requested magnitude, authored caps/scope, stable goal semantics, one owner-scoped input snapshot, strict guarded API, temporary browser result; no target or plan writes |
| Calorie proposals and targets | Immutable owner-scoped proposal snapshots, explicit approval with stale checks, migration 0008, one active target per owner, bounded private version history |
| Movement limitations | Explicit three-state self-report, migration 0009, private guarded API and browser form; no workout or medical clearance |
| Portion totals | Exact-ID gram rows, bounded input, retained raw/cooked identity, immutable contributions, missing nutrients preserved independently |
| Catalog seeds | Six pinned exercise records, complete equipment requirements, four sourced nutrient records, raw/cooked identity, exact-ID lookup, gram scaling, explicit blocked-food readiness, offline evidence check |
| Food preferences | Explicit allergy states and bounded names, diet, spending style, preparation allowance, custom local meal times, private atomic storage, guarded API, responsive form |
| Training preferences | Self-reported experience/activity, explicit equipment, Monday-based weekdays, bounded duration, owner-scoped atomic storage, strict API, responsive form |
| Weight goals | Server-selected starting snapshot, gain/loss/maintenance rules, one owner-scoped current goal, guarded API, responsive form, concurrent-retry protection |
| Basic profile | Plain Python validation, one owner-keyed profile per user, atomic saves, SQL bounds, protected API, responsive form, saved-value reload |
| HTTP controls | API/login rate limits, Retry-After, body/metadata/response bounds, safe response-validation errors, proxy-header rejection, local server limits |
| Database budgets | At most 10 pool connections, 3-second checkout wait, 5-second connection/statement bounds, 2-second lock bound |
| Browser privacy | Local assets, CSP, no-store, no-referrer, frame denial, same-origin policies, no access logging in the canonical launcher |
| Test isolation | Disposable socket-only PostgreSQL clusters, synthetic fixtures, migration round trips, unique browser-test cookie namespaces |

The profile's supported bounds are application input limits: age 18–120,
height 50–300 cm, weight 20–500 kg. These are not medical reference ranges.

## Database and Runtime Checkpoint

- The user supplied DATABASE_URL in the ignored local .env. Never print, copy into
  documentation, overwrite, or commit that value.
- The configured database connection was verified. Migration 0001 created users
  and login_sessions; migration 0002 added profiles; migration 0003 added goals;
  migration 0004 added training preferences; migration 0005 added food preferences.
  Migration 0006 adds explicit energy preferences. Migration 0007 adds pending
  calorie proposals. Migration 0008 adds approved calorie target versions;
  migration 0009 adds movement limitation answers. All were applied explicitly.
- Current expected migration revision: 0009. Existing accounts were preserved.
- Synthetic browser accounts and profiles were created only in disposable test
  clusters; those clusters were stopped and removed.
- The main local server was left running at http://127.0.0.1:8000. Do not assume
  its process survives until the next session or stop an unrelated process.
- Canonical launcher: `.venv/bin/python -m backend` from the repository root.
- Useful routes: /register, /login, /account, /profile, /goal, /training-preferences, /movement-limitations, /food-preferences, /energy-preferences, /calorie-preview, /calorie-proposals, /calorie-targets, /health.
- APIs: POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/logout,
  GET/PUT /api/profile, GET/PUT /api/goal, GET/PUT /api/training-preferences,
  GET/PUT /api/movement-limitations, GET/PUT /api/food-preferences,
  GET/PUT /api/energy-preferences, GET /api/energy-estimate,
  POST /api/calorie-preview, GET/POST /api/calorie-proposals,
  GET /api/calorie-proposals/{proposal_id}, POST approval by proposal ID,
  and GET active/history calorie target reads.

## Verification Already Performed

Latest complete application check:

```bash
.venv/bin/python scripts/test_postgres.py
```

Latest result: 206 working-tree tests passed, none skipped (2026-11-06). Coverage includes account/session isolation,
expiry/rotation/revocation, ownership and mass-assignment attempts, strict input,
profile persistence, SQL constraints/timeouts, rate limits, slow/chunked requests,
proxy spoofing, response leak prevention, and migration/model parity.

`pip check` passed. PyPA pip-audit 2.10.1 checked all 29 pinned packages against
the PyPI advisory service on 2026-10-29 and reported no known vulnerabilities.
The snapshot is [docs/dependency-audit.json](docs/dependency-audit.json). This does
not establish complete security; advisory data and dependency versions can change.

Browser checks used synthetic data: registration → sign-in → basic profile → save
→ reload → invalid time-zone update → reload → logout. Values persisted and the
invalid update preserved the old profile. Desktop/mobile layouts were inspected.
Live HTTP checks confirmed no Server header, no-store responses, and rejection
of spoofed X-Forwarded-For headers. Details are in docs/verification.md.

The 2026-10-29 and end-of-day 2026-10-30 handoffs were documentation-only.
The latest 2026-11-05 implementation passed the complete working-tree suite. Re-run relevant
checks when code or runtime configuration changes.

## Git Checkpoint and Completed Increments

Repository: https://github.com/mukhammaddiyor01/trainAI

The original 2026-10-29 handoff followed 0682f78 and was committed as dfe7b23.
The 2026-10-30 handoff is a1a045d; the training-preference checkpoint is 335862a.
The food-preference checkpoint is b5d4a3c; catalog documentation is fc89ac6,
followed by handoff dd69dc4. Allergy readiness handoff is f5b59ce. The latest
implementation is edb3c7b on develop, after proposal discovery storage/API
commits 8842965 and c8f1aa6. The earlier proposal API is e818b9a, after boundary/schema/storage
commits 4d184d0, f7656ad, and 0b26d80. The prior preview API is 589bb99 after policy/service
increments 4d50a97 and b76ecfa. The energy onboarding handoff is cbb64c0;
its initial service handoff is ca710a4, and the portion checkpoint is da04b5a.
Master remains at a8ddfd9, the initial web setup. Subsequent work belongs only on
develop. Each verified milestone ends with a separate documentation checkpoint.

| Commit | Completed increment |
| --- | --- |
| fb0fe5e | Development rules committed before application code |
| a8ddfd9 | Verified FastAPI web foundation |
| 32da617 | Explicit PostgreSQL connection management |
| b7c3842 | Account and login-session migrations |
| bf97609 | Account validation and Argon2 password hashing |
| 113c269 | Persistent authenticated identities and expiring sessions |
| cfec531 | Protected authentication HTTP endpoints |
| 461e8b6 | Registration/sign-in/account screens |
| b7318d2 | Strict authentication request and response schemas |
| 5f17e45 | Shared identity and origin guards |
| bed4080 | Bounded rolling-window credential throttling |
| c26a0bb | HTTP resource bounds and sanitized response failures |
| b858810 | Plain Python basic-profile validation |
| 12da5f9 | Clean rejection of oversized profile integers |
| d2097f5 | Owner-scoped profile persistence and migration 0002 |
| 4e70c18 | Protected profile API and strict ownership validation |
| abfed38 | Responsive private profile form |
| 6e4f6e8 | Separate cookie namespaces for disposable browser tests |
| bbce96b | Bounded database pool waits and verified SQL timeouts |
| 0682f78 | Security/profile verification and dependency-audit documentation |
| dfe7b23 | Completed-work record and mandatory Markdown reading procedure |
| d211438 | Plain gain/loss/maintenance goal rules |
| 0430a53 | Explicit targeted isolated PostgreSQL checks |
| 5005558 | Stable owner-scoped goal snapshots and migration 0003 |
| fcd81ac | Strict guarded goal API |
| 15b413e | Responsive goal onboarding and saved context |
| e5ce7d5 | User-selected 8-character password policy across all layers |
| 222f637 | Verified goal milestone, resolved password decision, and next preference steps |
| a1a045d | End-of-day handoff and next-session checklist |
| fba243c | Plain training-preference rules and immutable selections |
| a2c320d | Owner-scoped preference storage and migration 0004 |
| bbc60c9 | Guarded preference API, strict validation, and request bounds |
| a5352bb | Responsive preference onboarding and saved selections |
| 335862a | Verified training-preference checkpoint and next food inputs |
| d79209d | Plain food-preference rules and explicit allergy states |
| 9fd6e57 | Private food-preference storage and migration 0005 |
| bb5a2d0 | Strict guarded food-preference API and allowlisted responses |
| bfc4c4d | Food onboarding and editable local meal times |
| b5d4a3c | Verified food-preference checkpoint and next catalog inputs |
| 7755ab0 | Pinned exercise seeds and complete equipment validation |
| ec3355b | Sourced USDA nutrients and explicit unknown composition |
| a4436f8 | Exact catalog lookup, gram scaling, and readiness boundaries |
| 135a9ff | Verified official USDA API provenance links |
| 6175ce8 | Explicit offline source-evidence verification |
| d49579e | Reject prepared food nutrient/name drift against retained source |
| fc89ac6 | Verified catalog milestone and planning-readiness checkpoint |
| dd69dc4 | October 31 completed-work handoff and required next-session reading |
| 9179c9e | Bounded reviewed allergy-name vocabulary and shared normalization |
| 7d3ade6 | Preserve unresolved allergy names in food-readiness checks |
| 3350355 | Offline registry validation and pending composition counts |
| f5b59ce | Verified allergy-name readiness and composition-review handoff |
| 3102a4e | Composition-source review outcome and product evidence requirements |
| 3ed98b3 | Bounded multi-portion nutrient totals and focused regression tests |
| da04b5a | Verified portion-total handoff and next calculation-input review |
| 906e1c8 | Reviewed adult energy method, source coefficients, and explicit input scope |
| f57b3e7 | Strict immutable energy calculation preferences without defaults |
| 14b5845 | Versioned adult DRI 2023 estimate with scope checks and independent fixtures |
| ca710a4 | Verified adult energy services and private-collection handoff |
| e6c2fd2 | Private energy preferences and additive migration 0006 |
| 96ebe4c | Strict guarded three-field energy-preference API |
| d8acc04 | Owner-scoped current-input estimate API and one-snapshot read |
| 1e55091 | Explicit responsive energy form and saved estimate view |
| cbb64c0 | Verified private energy onboarding and migration checkpoint |
| 4d50a97 | Calorie-preview evidence review and authored application limits |
| b76ecfa | Explicit bounded calorie preview service without target activation |
| 589bb99 | Guarded preview API and single-snapshot owner inputs |
| d7f70f6 | Explicit calorie preview browser flow |
| e48855d | Verified preview UI handoff |
| 4d184d0 | Pending proposal storage and approval boundary |
| f7656ad | Pending-only proposal table and migration 0007 |
| 0b26d80 | Locked owner-scoped proposal snapshot storage |
| e818b9a | Strict guarded pending proposal create/read API |
| 0ce484e | Private pending proposal review page and owner isolation |
| 2b6c47a | Explicit preview-to-pending-save browser action |
| b8ba7d6 | Verified pending proposal browser-flow handoff |
| 8842965 | Bounded owner-scoped pending proposal keyset storage |
| c8f1aa6 | Guarded allowlisted pending proposal list API |
| edb3c7b | Private saved proposal list and navigation |

## Historical Password Edit — Resolved on 2026-10-30

During the 2026-10-29 handoff, an uncommitted edit lowered the service minimum
from 15 to 8 while the HTTP schema and UI still required 15. The edit was preserved.
On 2026-10-30, the user explicitly selected an 8-character minimum. Service, schema,
and rendered forms now use shared 8/128 constants. The policy fix includes an
8-character registration/login check and 7-character rejection. No password-rule
edit remains pending. The previous 53-test result remains a historical snapshot.

## Decisions to Preserve

- Speak Uzbek with the user; keep code, interface, comments, commits, and project
  documentation in English.
- Verify and commit each small coherent logic change before starting the next.
  Do not combine services, migrations, API behavior, and UI into one large commit.
- Use only feat: and fix: prefixes. Push authorized completed work to develop;
  do not advance master without a new explicit instruction.
- Support multiple users. Every private operation requires server-side identity
  and owner-scoped persistence, not just a logged-in browser.
- Use metric units, explicit user time zones, Monday week boundaries, and
  customizable meal schedules as features arrive.
- OAuth is explicitly deferred. Keep local login; do not configure providers,
  create OAuth credentials, or claim social login works.
- Current rate limiting is per-process local memory. Public deployment and paid
  cloud training remain outside the authorized scope.
- Do not modify reference projects, expose private data, fabricate progress, or
  claim that the four-field basic profile is sufficient to generate a plan.

## Session Progress — 2026-10-30

- Read all 10 existing project Markdown documents before implementation and
  inspected the branch, history, and local password-rule diff.
- Preserved the local 8/15 mismatch until the user selected 8. The authorized
  policy fix now shares limits across service, schema, and UI.
- Added plain Python gain/loss/maintenance goal rules and immutable goal values.
  Three targeted rule tests passed. These checks do not claim the full application
  suite passes with the unrelated password edit still present.
- Added an explicit --pattern option to the isolated PostgreSQL runner. Its
  default remains full discovery. Two targeted profile-storage checks and the
  migration round trip passed; this is not a full-suite result.
- Added migration 0003 and owner-scoped goal storage with profile locking and
  stable starting-weight snapshots. Five targeted PostgreSQL checks passed,
  including concurrent retries, constraints, and migration/model parity.
- Added the protected strict goal API. Four targeted HTTP/ownership checks
  passed, covering missing profiles, forged owner/starting-weight fields,
  two-user isolation, invalid update rollback, and maintenance without a target.
- Added the responsive goal page and profile/account navigation. Two targeted
  page tests passed. Browser checks confirmed profile-first onboarding, invalid
  target feedback, save/reload, stable snapshots after a profile-weight change,
  maintenance without a target, and mobile layout. Synthetic test data was removed.
- Goal rules, persistence, API, and UI are now implemented. All 67 tests passed
  against exact committed snapshot 15b413e, excluding the then-pending local
  password edit. After the authorized 8-character policy fix, all 68 working-tree tests passed
  in the isolated PostgreSQL runner, with no skipped checks.
  Goals do not generate a plan, calorie target, or guaranteed date.
- Applied migration 0003 explicitly to the configured database, preserving users
  and profiles. The local runtime was restarted with the current code; anonymous goal-page/API
  access and the rendered 8-character minimum were checked on the live server.

## Session Progress — 2026-10-31

- Read all 11 existing project Markdown files before implementation; develop was
  clean and synchronized with origin/develop at a1a045d.
- Added plain Python training-preference validation, immutable values, and
  explicit application bounds. Four targeted service tests passed, covering
  malformed collections, duplicates, strict types, and detached input values.
  No activity multipliers or exercise recommendations are computed.
- Preference rules committed as fba243c. Added owner-scoped storage and reviewed
  migration 0004. Four targeted disposable PostgreSQL tests passed, covering
  round trips, two-owner isolation, concurrent retries, SQL bounds, and model
  parity; migration downgrade/upgrade also passed in the disposable cluster.
  Persistence committed as a2c320d. The configured real database is still at 0003.
- Added GET/PUT /api/training-preferences with shared guards, a 4096-byte body
  cap, strict schemas, and five-field responses. Five targeted tests passed,
  including two-user isolation, invalid-update preservation, malformed/oversized
  input, owner/role injection, and revoked access. API committed as bbc60c9.
- Added the responsive English preference form and navigation. Two targeted page
  tests passed. Browser verification confirmed profile-first onboarding, empty-day
  rejection, bodyweight save/reload, equipment/duration edits, stale-success
  clearing, desktop/mobile layouts without horizontal overflow, and logout.
  Synthetic records and the disposable cluster were removed.
- All 83 tests passed with no skips in isolated PostgreSQL, including migration
  round trips. UI committed as a5352bb.
- After confirming revision 0003 and no table conflict, explicitly applied the
  additive migration 0004 to the configured database. No existing tables were
  modified and no synthetic records were written there. `pip check` passed.
- Started the canonical loopback runtime and verified anonymous page/API guards,
  script delivery, no-store responses, and absent Server headers. The local
  process was left running; verify availability again next session.

## Food-Preference Continuation — 2026-10-31

- Read all 12 existing Markdown files and confirmed a clean develop at 335862a.
- Added plain food-preference rules and immutable values: explicit allergy status,
  bounded reported names, diet, spending style, preparation time, and custom
  local-clock meal times. Five targeted rule tests passed. No prices, calorie
  targets, food safety assessment, or meal plans are computed.
- Rules committed as d79209d. Added owner-scoped atomic persistence and additive
  migration 0005. Four targeted PostgreSQL tests and disposable migration round
  trips passed, covering SQL bounds, allergy consistency, two-owner isolation,
  replacement, concurrent retries, and metadata parity. The configured database
  remains at 0004. Storage committed as 9fd6e57.
- Added the guarded six-field food-preference API with an 8192-byte request cap.
  Five targeted tests passed: exact Origin/session guards, owner isolation,
  strict fields/types, redacted errors, canonical responses, invalid-update
  preservation, and malformed/oversized JSON. API committed as bb5a2d0.
- Added the English food-preference form, conditional reported-name field, local
  meal-time editor, profile-zone context, and account/training navigation. Fixed
  the template conditional caught by the initial page check; both page tests
  then passed, including reported-name HTML escaping.
- Browser checks used synthetic data: unsure/listed/none_reported transitions,
  duplicate-name rejection, canonical save/reload, explicit allergy-list clearing,
  meal-time add/remove bounds, stale-success clearing, and logout. Desktop/mobile
  layouts had no horizontal overflow; console inspection returned no warnings or
  errors. Temporary test records and the owned cluster were removed.
- All 99 application tests passed, none skipped, with isolated PostgreSQL and
  migration round trips. UI committed as bfc4c4d.
- Explicitly applied additive migration 0005 after verifying revision 0004 and
  no table conflict; existing tables were not modified. No synthetic data was
  written to the configured database. `pip check` passed.
- Restarted the owned loopback runtime with food routes. Anonymous page/API
  guards, local script delivery, no-store responses, and absent Server headers
  passed live checks. Dependencies were unchanged; advisory audit not rerun.

## Catalog Continuation — 2026-10-31

- Read all 13 existing Markdown files; develop was clean at b5d4a3c.
- Verified the exercise source's pinned commit and Unlicense dedication. Added
  six metadata seeds with retained source/license evidence, strict local loading,
  plain immutable values, and complete equipment requirements. Bench/bar needs
  omitted by upstream single labels were recorded explicitly.
- Four targeted catalog tests passed, covering provenance, equipment subsets,
  malformed metadata, duplicate IDs, JSON ambiguity, and resource bounds.
  This is not an exercise prescription. Exercise increment committed as 7755ab0.
- Retrieved four public USDA SR Legacy nutrient records with exact descriptions,
  100-g edible basis, raw/cooked distinctions, source IDs, retained responses,
  retrieval dates, CC0-1.0 provenance, and SHA-256 evidence. Missing composition,
  diet, and allergen metadata remain unknown; no automatic food selection is
  enabled. Five targeted tests passed for values/units, unknowns, identity,
  malformed records, and corrupt evidence. Food increment committed as ec3355b.
- Added exact-ID lookup, explicit gram scaling with preserved unknown nutrients,
  and readiness blockers for unresolved composition/diet/allergen metadata and
  allergy status/mapping. All current foods remain blocked from automatic
  selection. Five targeted use-rule tests passed. No plans or daily targets exist.
  Use-rule increment committed as a4436f8.
- Source-link verification found USDA web detail routes returned 404. Replaced
  them with the documented, successfully retrieved official API resource URLs
  using USDA's public DEMO_KEY. Five food-source tests passed after correction;
  runtime catalog loading remains offline. Source-link fix committed as 135a9ff.
- Added explicit offline catalog verification with exercise source-evidence
  parity and food snapshot digests. Two operator tests passed, including denied
  sockets and an unusable DATABASE_URL. The command reports 6 exercise and 4
  food nutrient records while clearly stating food selection is unavailable.
  Operator-check increment committed as 6175ce8.
- All 16 catalog checks passed; the complete isolated PostgreSQL suite passed
  115 tests, none skipped, including migration round trips. `pip check` passed.
  No dependencies/schema/UI/HTTP changes were introduced; configured migration
  remains 0005. The user database was not used, and browser/advisory checks were
  not repeated for this backend/data-only milestone.
- Strengthened food loading to compare identity, nutrient IDs, units, and amounts
  against the retained response, beyond matching its digest. A new regression
  rejects edited prepared values/names even when the original source hash stays
  unchanged. Six targeted food tests and the offline check passed. Fix committed
  as d49579e. All 17 catalog checks and the final complete 116-test suite passed,
  none skipped; the extra full run followed the source-parity change.

## Allergy-Name Continuation — 2026-11-02

- Read all 14 existing project Markdown files before implementation; develop was
  clean and synchronized with origin/develop at dd69dc4.
- Reviewed FDA Edition 5 and its current FAQ, and compared the evidence scope
  with the nutrient-only USDA records. A labeling reference does not establish
  food ingredient composition or allergy safety for those generic records.
- Added a deliberately bounded nine-group/fifteen-name English resolver using
  shared saved-name normalization, immutable versioned results, and preserved
  unknown names. Four targeted mapping tests and five existing food-rule tests
  passed. No fuzzy matching, translation, diagnosis, or food approval is performed.
  Resolver increment committed as 9179c9e.
- Integrated exact-name resolution into food readiness. Unsupported/partially
  recognized lists add allergy_names_unresolved; recognized names still retain
  the separate ingredient-mapping and food-composition blockers. Two new
  readiness regressions and all five original catalog-use tests passed. All
  current foods remain blocked; no personal data, API, or schema changed.
  Readiness increment committed as 7d3ade6.
- Inspected all four retained USDA records: no ingredient declaration or
  root-level allergen fields are present. No composition approval was inferred.
- Extended offline checks with registry ambiguity rejection, 9-group/15-term
  counts, mapping version, and 4 pending composition reviews. Five resolver and
  three operator tests passed; offline checks still work with sockets denied
  and DATABASE_URL unavailable. Offline-check increment committed as 3350355.
- The complete isolated PostgreSQL suite passed 124 tests, none skipped,
  including migration round trips. `pip check` passed. The configured database
  was not used; no dependency/schema/UI/HTTP changes were introduced. Browser
  and historical advisory checks were not rerun for this backend-only increment.
- A read-only startup check found no listener on port 8000. No server was
  started/stopped; the ambient port-8001 browser tab was not used or modified.

## Portion-Arithmetic Continuation — 2026-11-02

- Read all 15 project-owned Markdown files before implementation and confirmed
  clean, synchronized develop at f5b59ce.
- Rechecked USDA's official data-type comparison/API guide and all four retained
  snapshots. Recorded the composition review outcome as insufficient evidence,
  with per-source observations and explicit evidence requirements for a future
  product import. No nutrient-only record was approved or altered.
- Next small increment: bounded exact-ID multi-portion nutrient totals. This
  arithmetic is independent of food eligibility and personal daily targets.
- Composition-review decision committed separately as 3102a4e.
- Added nutrition_for_portions: 1–50 explicit (food ID, grams) rows, exact catalog
  lookup, existing positive finite gram bounds, source-based scaling, and fsum
  totals. Repeated rows are additive; raw/cooked IDs and individual contributions
  are retained in immutable results. Missing nutrient values propagate only to
  that nutrient total; empty input does not fabricate zero intake.
- Seven new portion-total tests and all seven existing use-rule/six food-catalog
  tests passed (20 targeted checks). Includes unknown-ID rejection without
  skipping rows, malformed/oversized collections, invalid masses, missing-vs-zero
  values, detached immutable results, and unchanged food-selection restrictions.
- This is plain offline arithmetic only, with no saved meal, recommendation,
  personal target, HTTP contract, schema, UI, or dependency change.
- Service increment committed as 3ed98b3. The full isolated PostgreSQL suite
  passed 131 tests, none skipped, with migration round trips and owned-cluster
  cleanup. pip check and explicit offline catalog verification also passed.
- No configured database access, migration, dependency, UI, or HTTP change was
  made. No server was started/stopped or browser check/advisory audit repeated.
- Next: reviewed calculation methods and required missing inputs before personal
  targets; separately supported product composition before automatic food selection.

## Energy-Method Continuation — 2026-11-02

- Read all 15 existing project-owned Markdown files before implementation; clean
  develop was synchronized at da04b5a. A read-only port-8000 check found no listener.
- Reviewed National Academies 2023 Table 5-16 and Health Canada's adult equations,
  units, and whole-day PAL definitions. Selected direct adult EER rather than
  applying unreviewed activity factors to resting energy. Documented explicit
  coefficient/activity/context inputs, source boundaries, and application scope
  in docs/energy-estimation.md before implementing calculations.
- Method/source review committed separately as 906e1c8.
- Added explicit immutable energy preferences: equation sex, whole-day activity
  category, and calculation context. No defaults/inference; unsure and excluded
  contexts remain representable without implying calculation eligibility.
- Four targeted rule tests passed, including all 75 supported combinations,
  missing/malformed/coercible inputs, training-label rejection, exact choices,
  redacted errors, and immutable unsure values. No estimate is computed yet.
- Input-rule increment committed as f57b3e7. Added the versioned adult EER
  service with all eight reviewed equations, current-profile validation, age-19
  boundary, explicit context/unknown checks, and nonpositive-result rejection.
  The output keeps method/selection metadata and unrounded kcal/day values.
- Eight targeted estimate tests passed, including independent fixtures for all
  equations, fractional values, all 67 uncertain/excluded choice combinations,
  age 18/19, forged dataclass values, current weight, time-zone independence,
  immutable results, and offline operation. No gain/loss offsets, food selection,
  plans, storage, API, or browser behavior were introduced.
- Calculation increment committed as 14b5845. All 143 isolated PostgreSQL tests
  passed, none skipped, with migration round trips and owned-cluster cleanup.
  pip check and the offline catalog check passed. No configured database access,
  schema/dependency/HTTP/UI change, server restart, browser check, or advisory
  audit was performed. No calorie target or plan was created.
- Next: private energy preference storage and reviewed migration, followed by
  guarded API and explicit input UI before any user-facing estimate.

## Energy-Onboarding Continuation — 2026-11-02

- Read all 16 existing Markdown files and confirmed clean develop at ca710a4.
- Added additive migration 0006 and one energy_preferences row per profile,
  with no defaults/backfill. Exact non-null SQL choices preserve unsure and
  excluded contexts. Atomic complete-row upserts return validated plain values.
- Four targeted disposable PostgreSQL tests passed: all 75 choice combinations,
  owner isolation, invalid-update preservation, concurrent complete selections,
  SQL bounds/nulls/foreign key/cascade, and model/migration parity. Disposable
  migration round trips passed. Configured database not used at this increment.

- Storage increment committed as e6c2fd2. Added GET/PUT /api/energy-preferences
  with shared identity/Origin guards, a 2048-byte JSON cap, exact three-field
  strict input/response schemas, and profile-first writes. Five targeted API
  checks passed in disposable PostgreSQL, covering two-user isolation, owner and
  calculated-field injection, revoked access, malformed/oversized JSON, redacted
  errors, and invalid-update preservation. Migration round trips passed.

- Preference API committed as 96ebe4c. Added read-only /api/energy-estimate,
  with a single owner-scoped joined profile/preference query and four-field
  strict response. Inputs are revalidated; missing inputs return 404 and scope
  exclusions return 409. Estimates are recomputed from current weight, without
  saved calorie targets or goal-baseline substitution.
- Four targeted estimate API tests passed in disposable PostgreSQL, including
  identity/query spoofing, two-owner isolation, current-weight vs goal snapshot,
  response allowlisting, uncertainty/context/age/nonpositive exclusions, and
  revoked access. Disposable migration round trips passed.

- Estimate endpoint committed as d8acc04. Added /energy-preferences with explicit
  choices, source/category guidance, saved current-profile estimate or truthful
  unavailable state, account/food navigation, local styles/scripts, and stale
  success/result clearing. Reused existing palette/type/form patterns after
  reading frontend-design. Two targeted page tests passed in disposable PostgreSQL.
- Synthetic browser flow passed: registration/sign-in, profile-first redirect,
  profile save, empty choices, unsure save/reload, eligible estimate save/reload,
  clinical exclusion, edit-time stale-result clearing, category-guide disclosure,
  and logout protection. No horizontal overflow at inspected effective widths
  355 and 1164 CSS px (requested 390/1280); no console warnings/errors. Viewport
  overrides reset. Only the owned disposable browser instance was used.
- UI increment committed as 1e55091. Full disposable PostgreSQL regression passed
  158 tests, none skipped, with migration round trips and cleanup. pip check and
  offline catalogs passed. The owned browser test cluster/data/tab were removed.
- Verified configured revision 0005 and no energy_preferences conflict; applied
  additive migration 0006 and checked its four columns. Existing records were
  not modified and no synthetic data was written to the configured database.
- Started the canonical bounded loopback server on port 8000. Live login/script
  checks returned 200, anonymous energy page 303 to login, and both energy APIs
  401, all with no-store and no Server header. A sandbox-restricted first probe
  was retried successfully with authorized local network access.
- No new dependency or advisory audit. Runtime remains available; prescriptions,
  plans, and food selection remain outside this completed onboarding increment.

## Calorie-Preview Continuation — 2026-11-04

- Read all 16 project-owned Markdown files; develop was clean and synchronized
  at cbb64c0. No listener was observed on ports 8000/8001 during the startup check.
- Reviewed official NICE/NHS/NIDDK guidance and recorded source limitations and
  authored product bounds before implementation in docs/calorie-preview.md.
  The preview requires an explicit requested adjustment; no universal offset,
  clinical safety, nutrient adequacy, completion date, or approval is inferred.
- Policy review committed as 4d50a97. Added plain explicit-request previews with
  strict magnitude/direction checks, current DRI estimate, saved-goal revalidation,
  BMI scope, relative/absolute caps, and result floor. Excess requests are rejected
  without clamping; reached/crossed goals require review without rewriting them.
- Eight targeted tests passed for gain/loss/maintenance arithmetic, malformed
  requests, caps/floor/BMI boundaries, stable goal snapshots, missing/forged and
  ineligible inputs, precision, immutable preview status, and offline execution.
- Service increment committed as b76ecfa. Added POST /api/calorie-preview with
  exact-Origin/session guards, strict one-field input, 2048-byte JSON cap, seven
  allowlisted output fields, and one joined owner-scoped profile/preference/goal
  snapshot. No target or plan is written and no default adjustment is inferred.
- Five targeted API checks and isolated migration round trips passed, including
  two-owner isolation, identity/result injection, revoked access, no input mutation,
  strict/ambiguous/oversized JSON, scope changes, and current weight vs goal baseline.
- API increment committed as 589bb99. Full isolated suite passed 171 tests, none
  skipped, with migration round trips and owned-cluster cleanup. pip check and
  offline catalogs passed. No schema/dependency/UI changes or configured database
  access occurred; no browser check/advisory audit was repeated.
- Started the capped canonical loopback server on port 8000. Live login returned
  200; preview without Origin returned 403 and same-Origin anonymous preview 401,
  all with no-store and no Server header. No private records were read/written.
- Next: explanatory preview UI, then separately reviewed proposal persistence and
  transactional approval/versioning. No calorie target or plan was activated.

## Next Work — Not Yet Completed

The reference catalog seed milestone is complete. Continue the original
profile → weekly plan → daily logging → weekly review → approved revision flow:

1. Review exercise prescription rules and user limitations before turning
   equipment candidates into workouts. Upstream source levels are not suitability
   approval. The calorie target approval milestone is complete; a calorie target
   does not create a weekly plan. See docs/calorie-approval.md.
2. Obtain separately identified product ingredient/diet/allergen evidence before
   automatic food selection. The current four composition-source reviews found
   insufficient evidence; do not repeat generic nutrient retrieval as if it
   supplies product composition. All four seeds remain nutrition-only and blocked.
   Unknown/ambiguous allergy names remain unresolved.
3. Review deterministic plan calculation inputs and safe failure states before
   connecting nutrition and exercise candidates into a weekly plan.
4. Build deterministic plan rules after inputs/catalogs are sufficient; then add
   owner-scoped persistence, guarded API, and UI in separate verified commits.

Later work remains: catalog expansion/composition review; verified calculation methods;
deterministic plans; daily logs; weekly review and approved plan versions;
TinyLlama/tokenizer integration; licensed datasets; LoRA/SFT and evaluation;
OpenCV plus a separately reviewed pose model; complete fitness-flow verification.
No model weights, AI inference, training, camera tracking, or workout/nutrition
plans are implemented or verified yet. Explicitly approved daily calorie target
versions use the existing experimental calorie preview policy.

## End-of-Day Handoff — 2026-10-30

- Re-read all 11 current project Markdown files and reconciled this record with
  the clean develop branch and recent commits. No application code changed.
- The goal milestone and selected 8–128-character password policy are complete.
  There is no pending password decision or local password-rule edit.
- The latest application baseline remains the 68 passing isolated checks recorded
  above; application tests and the dependency audit were not rerun for this
  documentation-only handoff.
- Next planned continuation: 2026-10-31 (Asia/Seoul), when the user resumes work.
  First read every project-owned Markdown file, including any newly added files;
  then inspect user changes, branch state, and runtime availability.
- At this handoff, the first next implementation increment was plain Python training-preference
  validation. Persistence, API, and UI follow as separate verified commits.
  Do not start those features as part of this handoff.
- This file preserves the project checkpoint for the next session. No automatic
  task or scheduled continuation has been created.

## Resume Checklist

- Read every project-owned Markdown file before code changes.
- Inspect git status, current branch, recent commits, and any user changes.
- Check runtime/database availability without exposing secrets or recreating data.
- Preserve the last verified baseline and select one small next increment.
- Implement, verify, update this record, and commit that increment separately.

## Calorie target approval and version history — 2026-11-06

- Read all 18 project-owned Markdown files before implementation. Started from
  clean synchronized `develop` at ae1d787. Recorded the approval boundary in
  `docs/calorie-approval.md` (738c596).
- Migration 0008 adds proposal approval lifecycle and constrained target version
  storage, including one active version per owner (c567eef). Proposal creation
  snapshots the current active version for stale-approval detection (93efe69).
- Transactional service locks owner inputs, revalidates source snapshots and
  recalculates the preview, supersedes the old version, and supports idempotent
  retries (bb9a8b5). The API requires strict exact-true confirmation and owner
  guards (08734ef); version history is bounded and private (1dbc3a4).
- The private proposal detail now offers explicit approval only while pending;
  approved and superseded versions appear truthfully in the detail, list, and
  target history pages (655ca7c). It creates a daily experimental calorie target,
  not a workout, meal, or weekly plan. OAuth remains deferred.
- Full disposable PostgreSQL regression passed 196 tests, none skipped, with
  downgrade/upgrade round trips. The configured database was checked at 0007
  without a target table and explicitly upgraded to 0008. Schema metadata only
  was inspected; no real user records or secrets were read or written.
- An isolated browser visit confirmed anonymous `/calorie-targets` redirects to
  login. The temporary tab, server, and test cluster were removed. Manual signed-in
  browser approval remains a verification gap; automated owner/page/API tests pass.
- `pip check` and offline catalog verification passed. The updated bounded
  loopback server was started on port 8000; live anonymous checks returned 303
  for the target page and 401 for both target read APIs, with `no-store` and
  no `Server` response header.
- Next: review exercise rules and limitations, then independently review missing
  food composition evidence before any automatic plan selection. Do not claim
  the approved calorie target is a full plan or clinical recommendation.
