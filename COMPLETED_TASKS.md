# TrainAI — Completed Tasks and Session Handoff

Last updated: 2026-10-30 (Asia/Seoul).
Session resumed on 2026-10-30 after reading all project-owned Markdown files.

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
- [Security boundaries](docs/security.md)
- [Verification history](docs/verification.md)

AGENTS.md and this handoff describe the latest agreed state. Some documents retain
earlier milestone observations: the 7-test and 29-test results are historical;
the latest complete suite passed 53 tests. If documents disagree, inspect Git
history and current code before proceeding. Do not silently assume which is right.

## Confirmed Working State

The application supports account registration, sign-in/sign-out, private session
identity, and a basic private profile containing age, height, weight, and IANA time
zone. Goals and full planning preferences have not been implemented.

| Area | Completed behavior |
| --- | --- |
| Foundation | FastAPI composition, Jinja2 pages, local HTML/CSS/JavaScript, responsive English UI, web-only health endpoint |
| Persistence | Explicit PostgreSQL configuration, SQLAlchemy transactions, connection check, reviewed Alembic migrations, no SQLite fallback or startup schema creation |
| Registration | Canonical unique usernames, input rules, salted Argon2id password hashes, generic failures without input/credential exposure |
| Sessions | Random 32-byte tokens, SHA-256 digests in storage, 24-hour expiry, login rotation, logout revocation, HttpOnly/host-only/SameSite cookies |
| Guards | Shared same-origin write checks and server-derived account identity; browser user_id, role, or forged Bearer values do not establish identity |
| Validation | Strict Pydantic request/response contracts, unknown-field rejection, no coercion, bounded UTF-8 JSON, duplicate-key/non-finite/compressed-body rejection |
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
  and login_sessions; migration 0002 added profiles. Both were applied explicitly.
- Current expected migration revision: 0002. Existing accounts were preserved.
- Synthetic browser accounts and profiles were created only in disposable test
  clusters; those clusters were stopped and removed.
- The main local server was left running at http://127.0.0.1:8000. Do not assume
  its process survives until the next session or stop an unrelated process.
- Canonical launcher: `.venv/bin/python -m backend` from the repository root.
- Useful routes: /register, /login, /account, /profile, /health.
- APIs: POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/logout,
  GET /api/profile, and PUT /api/profile.

## Verification Already Performed

Latest complete application check:

```bash
.venv/bin/python scripts/test_postgres.py
```

Result: 53 tests passed, none skipped. Coverage includes account/session isolation,
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

This handoff update changes documentation only; it does not represent a new test
run. Re-run relevant checks when code or runtime configuration changes.

## Git Checkpoint and Completed Increments

Repository: https://github.com/mukhammaddiyor01/trainAI

Before this documentation update, develop and origin/develop pointed to 0682f78.
Master remains at a8ddfd9, the initial web setup. Subsequent work belongs only on
develop. This handoff and its startup rule are a separate documentation commit.

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

## Uncommitted Change Observed During This Handoff

A local edit appeared in backend/services/accounts.py while the documentation was
being prepared: validate_password now accepts a minimum of 8 characters instead
of the committed 15-character minimum. This edit was not made, reverted, tested,
staged, or committed as part of the documentation task.

The HTTP Credentials schema, browser forms, documentation, and existing tests
still use a 15-character minimum. Therefore the last 53-test result describes the
committed implementation before this local edit, not a newly verified working
tree. Preserve the edit. At the next session, inspect the actual diff and clarify
the intended password policy with the user before changing or committing it.
Do not automatically harmonize the other layers to the shorter value.

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
- Asked the user to resolve the pending 8/15-character password policy; the local
  edit remains untouched while that answer is pending.
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
- Goal rules, persistence, API, and UI are now implemented. The full committed-code
  snapshot is the next verification step; the local password edit remains pending. Goals do not
  generate a plan, calorie target, or guaranteed date.

## Next Work — Not Yet Completed

The immediate next milestone is goals and planning preferences. Start with the
smallest independently testable increment after reading all Markdown files:

1. Define plain Python goal rules for gain, loss, and maintenance; decide how to
   represent current versus target weight without promising a result/date.
2. Add only the persistence and reviewed migration needed by that goal feature.
3. Add a strict, bounded API using existing guards and owner-scoped queries;
   test two-user isolation, invalid input, and mass assignment.
4. Add the corresponding usable UI and verify it before its separate commit.
5. Introduce experience, activity, equipment, available days, duration, food
   preferences, allergies, budget, preparation time, and meal times incrementally.

Later work remains: sourced exercise/food catalogs; verified calculation methods;
deterministic plans; daily logs; weekly review and approved plan versions;
TinyLlama/tokenizer integration; licensed datasets; LoRA/SFT and evaluation;
OpenCV plus a separately reviewed pose model; complete fitness-flow verification.
No model weights, AI inference, training, camera tracking, calorie targets, or
workout/nutrition plans are implemented or verified yet.

## Resume Checklist

- Read every project-owned Markdown file before code changes.
- Inspect git status, current branch, recent commits, and any user changes.
- Check runtime/database availability without exposing secrets or recreating data.
- Preserve the last verified baseline and select one small next increment.
- Implement, verify, update this record, and commit that increment separately.
