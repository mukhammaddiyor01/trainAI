# TrainAI — Completed Tasks and Session Handoff

Last updated: 2026-11-02 (Asia/Seoul).
The 2026-11-02 continuation read all 14 existing project-owned Markdown files
before implementation. New milestone documentation is included in the inventory.

## Latest Session Handoff — 2026-10-31

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
- [Security boundaries](docs/security.md)
- [Verification history](docs/verification.md)

AGENTS.md and this handoff describe the latest agreed state. Some documents retain
earlier milestone observations: the 7-test and 29-test results are historical;
the latest complete working-tree suite passed 116 tests on 2026-10-31. If documents disagree, inspect Git
history and current code before proceeding. Do not silently assume which is right.

## Confirmed Working State

The application supports account registration, sign-in/sign-out, private session
identity, and a basic private profile containing age, height, weight, and IANA time
zone, gain/loss/maintenance weight goals, and private training preferences.
Private food preferences and custom local meal schedules are implemented.
Six sourced exercise metadata records and four USDA nutrient seeds are implemented.
Calculation-specific inputs, food composition/allergen review, and plans remain pending.

| Area | Completed behavior |
| --- | --- |
| Foundation | FastAPI composition, Jinja2 pages, local HTML/CSS/JavaScript, responsive English UI, web-only health endpoint |
| Persistence | Explicit PostgreSQL configuration, SQLAlchemy transactions, connection check, reviewed Alembic migrations, no SQLite fallback or startup schema creation |
| Registration | Canonical unique usernames, input rules, salted Argon2id password hashes, generic failures without input/credential exposure |
| Sessions | Random 32-byte tokens, SHA-256 digests in storage, 24-hour expiry, login rotation, logout revocation, HttpOnly/host-only/SameSite cookies |
| Guards | Shared same-origin write checks and server-derived account identity; browser user_id, role, or forged Bearer values do not establish identity |
| Validation | Strict Pydantic request/response contracts, unknown-field rejection, no coercion, bounded UTF-8 JSON, duplicate-key/non-finite/compressed-body rejection |
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
  All were applied explicitly.
- Current expected migration revision: 0005. Existing accounts were preserved.
- Synthetic browser accounts and profiles were created only in disposable test
  clusters; those clusters were stopped and removed.
- The main local server was left running at http://127.0.0.1:8000. Do not assume
  its process survives until the next session or stop an unrelated process.
- Canonical launcher: `.venv/bin/python -m backend` from the repository root.
- Useful routes: /register, /login, /account, /profile, /goal, /training-preferences, /food-preferences, /health.
- APIs: POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/logout,
  GET/PUT /api/profile, GET/PUT /api/goal, GET/PUT /api/training-preferences, and GET/PUT /api/food-preferences.

## Verification Already Performed

Latest complete application check:

```bash
.venv/bin/python scripts/test_postgres.py
```

Latest result: 116 working-tree tests passed, none skipped (2026-10-31). Coverage includes account/session isolation,
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
The latest 2026-10-31 implementation passed the complete working-tree suite. Re-run relevant
checks when code or runtime configuration changes.

## Git Checkpoint and Completed Increments

Repository: https://github.com/mukhammaddiyor01/trainAI

The original 2026-10-29 handoff followed 0682f78 and was committed as dfe7b23.
The 2026-10-30 handoff is a1a045d; the training-preference checkpoint is 335862a.
The food-preference checkpoint is b5d4a3c. The latest implementation commit is
d49579e on develop, followed by verified catalog documentation fc89ac6.
Both were pushed to origin/develop; the separate increments are listed below.
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

## Next Work — Not Yet Completed

The reference catalog seed milestone is complete. Continue the original
profile → weekly plan → daily logging → weekly review → approved revision flow:

1. Review ingredient/diet/allergen composition evidence and a deliberately bounded
   allergy-name mapping. Current USDA seeds are nutrition-only and must remain
   blocked from food selection until that review is complete.
2. Review calculation methods and required missing profile inputs before adding
   deterministic targets. Descriptive activity/budget labels are not verified
   multipliers, prices, or medical conclusions.
3. Review exercise prescription rules and user limitations before turning equipment
   candidates into workouts. Upstream source levels are not suitability approval.
4. Build deterministic plan rules after inputs/catalogs are sufficient; then add
   owner-scoped persistence, guarded API, and UI in separate verified commits.

Later work remains: catalog expansion/composition review; verified calculation methods;
deterministic plans; daily logs; weekly review and approved plan versions;
TinyLlama/tokenizer integration; licensed datasets; LoRA/SFT and evaluation;
OpenCV plus a separately reviewed pose model; complete fitness-flow verification.
No model weights, AI inference, training, camera tracking, calorie targets, or
workout/nutrition plans are implemented or verified yet.

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
