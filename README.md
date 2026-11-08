# TrainAI

A fitness planning application for adults working toward weight gain, weight
loss, or weight maintenance. The intended workflow is:

**Profile → weekly plan → daily log → weekly review → approved plan revision.**

## Session handoff

Read [COMPLETED_TASKS.md](COMPLETED_TASKS.md) for completed increments and the
resume checkpoint. Before continuing implementation, read all project-owned
Markdown files as required by [AGENTS.md](AGENTS.md).

## Current status

The web foundation and account access are implemented: responsive English pages,
registration, Argon2id password hashing, server-side sessions, sign-in/sign-out,
and private account identity. PostgreSQL schema changes use explicit Alembic
migrations. A private basic profile stores age, height, weight, and time zone.
Owner-scoped gain, loss, and maintenance goals and training preferences are available.
Food preferences and custom local meal times are also available. A small offline
catalog contains six sourced exercise metadata records and four USDA nutrient
records with explicit raw/cooked identity and source evidence. A bounded English
allergy-name resolver preserves unknown terms and reports unresolved readiness;
recognized names do not establish ingredient or allergy safety. Plain services
can total explicitly supplied food portions, preserving missing nutrient values;
this calculation does not recommend foods or set daily intake targets.
A reviewed DRI 2023 adult energy estimate is available after explicitly saving
private energy preferences. Strict owner-scoped APIs and the responsive form
preserve uncertainty and scope checks. The estimate uses the current profile and
does not create a gain/loss target or plan. See [energy inputs](docs/energy-estimation.md).
A protected explicit-request calorie preview API and browser form are available;
they write no target or plan. Experimental bounds are documented in
[preview policy](docs/calorie-preview.md).
Authenticated users can save a private calorie proposal from the preview and
find it later in a private, paged list. Explicit approval rechecks its snapshot
and activates a versioned daily target; prior versions remain visible in a bounded
private history. A target is an experimental estimate, not a meal or workout plan.
See [proposal boundary](docs/calorie-proposals.md) and
[approval boundary](docs/calorie-approval.md).
An explicit private movement limitation answer can now be saved as unsure,
none reported, or needs adaptation. It does not assess medical fitness or create
a workout; see [movement limitation boundary](docs/movement-limitations.md).
Plain scheduling logic can enumerate recovery-spaced pairs from saved available
weekdays without choosing a schedule; see [scheduling boundary](docs/workout-scheduling.md).
An [exercise readiness gate](docs/exercise-readiness.md) keeps all six metadata
records out of automatic selection until suitability and dosage are reviewed.
Fitness planning, logging, AI inference, training,
and camera tracking are not implemented yet.

## Local setup

Verified with Python 3.12 on Apple Silicon. Use an isolated environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt -c constraints.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m backend
```

Open http://127.0.0.1:8000. Stop the server with Ctrl+C. Run commands from the
repository root. The public introduction and login pages open without database
configuration; registering or signing in requires PostgreSQL.

Create a local ignored `.env` with DATABASE_URL, using the empty `.env.example`
as a reference. Do not overwrite an existing `.env` or put credentials in Git.
See [database setup](docs/database.md) before running explicit migrations:

```bash
.venv/bin/python -m backend.check_database
.venv/bin/python -m alembic upgrade head
```

Open `/register` to create your own account, `/login` to sign in, and `/account`
to view your private account. Open `/profile` to save your basic details, then
`/goal` to record your weight goal. Use `/training-preferences` to save experience,
activity, available equipment, weekdays, and session duration. Use
`/movement-limitations` to report whether activity needs adaptation, then
`/food-preferences` for diet, reported allergies, spending style, preparation time,
and meal times in your profile zone. Open `/energy-preferences` to save the
three explicit calculation choices and view an eligible daily energy estimate.
Open `/calorie-preview` to request an adjustment after saving a profile, goal,
and energy choices. The preview is temporary; use **Save pending proposal** to
store a reviewable snapshot, then open `/calorie-proposals` to find it again.
Review its detail page and explicitly choose **Approve calorie target** to
activate it. `/calorie-targets` shows the latest 20 approved versions. A preview
or saved pending proposal does not activate a target. Passwords
must be 8–128 characters. Registration does not automatically sign in. No real user data belongs in test fixtures.

For all 214 checks, including PostgreSQL integration, use the disposable runner:

```bash
.venv/bin/python scripts/test_postgres.py
```

Ordinary unittest discovery skips database integration checks unless the explicit
disposable test configuration is set. For isolated manual browser testing:

```bash
.venv/bin/python scripts/test_postgres.py --serve
```

This serves a separate temporary application on port 8001, with its own disposable
PostgreSQL cluster. Ctrl+C removes its test data. It never uses the real `.env`
database. No model downloads or camera permissions are needed.

`GET /health` reports web-process health only. Its `ai: not_configured` value
does not indicate model or database readiness. The app mounts only
`frontend/static/`, rejects unexpected hosts, and uses local assets without
third-party frontend requests.

## Structure

```text
backend/
  __main__.py             Local server with transport limits
  main.py                 Application composition and browser policies
  routes.py               Public page and health controllers
  auth_routes.py          Bounded authentication API
  profile_routes.py       Private profile API
  goal_routes.py          Private goal API
  training_preference_routes.py  Private training-preference API
  account_pages.py        Authenticated browser pages
  guards.py               Session and same-origin guards
  schemas.py              Strict input and public output contracts
  profiles.py             Owner-scoped profile persistence
  goals.py                Stable owner-scoped goal snapshots
  training_preferences.py Owner-scoped preference persistence
  services/               Plain Python profile, goal, and preference validation
  models.py               Account, session, profile, goal, and preference records
frontend/
  templates/              Introduction, authentication, profile, goal, and preference pages
  static/                 Local styles and browser scripts
tests/                    Isolated service, security, HTTP, and database checks
docs/
  architecture.md         Layer boundaries and staged implementation
  environment.md          Verified dependencies and hardware limitations
```

Account-input services, SQLAlchemy account/session models, migration files,
authentication controllers, and private account pages are now present. Fitness
services and AI/vision adapters will be introduced with their features.
See [database configuration](docs/database.md), [architecture](docs/architecture.md),
[environment](docs/environment.md), [authentication](docs/authentication.md),
[goals](docs/goals.md), [training preferences](docs/training-preferences.md),
[food preferences](docs/food-preferences.md), and
[development rules](AGENTS.md).

## Offline catalog check

```bash
.venv/bin/python -m backend.check_catalogs
```

This validates bundled source evidence without network or database access. Exact
IDs, complete equipment requirements, and gram-based nutrient scaling are available
in plain services. Current foods have unresolved ingredient/diet/allergen metadata,
so they are blocked from automatic selection. The command also checks 9 reviewed
allergy-name groups/15 exact terms, reports the mapping version, and shows 4 pending
composition reviews. See [catalog provenance](docs/catalogs.md) and
[allergy-name scope](docs/allergen-names.md).

## Next milestone

Review exercise-specific eligibility and dosage before generating workouts.
The four current composition-source reviews found insufficient evidence; separately
identified product composition and ingredient/allergen/diet evidence remain
required before automatic food selection or meal planning. Expand the bounded
allergy-name vocabulary only after reviewing each additional term. Unknown allergy
information must remain unknown. Metric
units, explicit IANA time zones, Monday weeks, and custom local meal times are
confirmed product defaults.
Use only synthetic data in tests; never commit real profiles or activity records.

## Security controls

Strict Pydantic input models, shared session/origin guards, owner-scoped profile
operations, explicit public response models, login/API rate limits, bounded JSON
bodies and response sizes, body/query/pool timeouts, proxy-header rejection, and
browser security headers are implemented. Use `python -m backend` for the capped
local launcher. Rate limits currently apply to one process, not multiple workers.

OAuth is deferred by the user's choice. See [security boundaries](docs/security.md)
and [basic profiles](docs/profiles.md). A 2026-10-29 pip-audit run checked all
29 pinned dependencies and reported no known advisories. This is a point-in-time
dependency result, not a complete security assessment.


## Explicit calorie preview API

POST /api/calorie-preview requires a signed-in owner, the exact page Origin, and
an application/json body containing only adjustment_kcal. It reads the saved
profile, energy preferences, and goal in one owner-scoped snapshot. No default
magnitude is supplied. The API returns a seven-field versioned preview or a
bounded error; it does not update inputs, store a target, or create/approve a plan.
See [scope and experimental limits](docs/calorie-preview.md) before use.

## Pending calorie proposal API

POST /api/calorie-proposals uses the same explicit adjustment-only input, exact
Origin, authentication, and strict 2048-byte JSON limit. It recomputes from locked
current saved inputs and creates a pending private snapshot. GET
/api/calorie-proposals/{proposal_id} returns that owner's nine-field summary.
`POST /api/calorie-proposals/{proposal_id}/approve` requires `{"confirm":true}`
and revalidates the owner snapshot before activation. `GET /api/calorie-targets/active`
reads the active version; `GET /api/calorie-targets` lists the latest 20 versions.
Migration 0008 is required. Repeated proposal-create POSTs create separate
pending records; retrying approval of the same proposal returns its original version.
