# TrainAI

A fitness planning application for adults working toward weight gain, weight
loss, or weight maintenance. The intended workflow is:

**Profile → weekly plan → daily log → weekly review → approved plan revision.**

## Current status

The web foundation and account access are implemented: responsive English pages,
registration, Argon2id password hashing, server-side sessions, sign-in/sign-out,
and private account identity. PostgreSQL schema changes use explicit Alembic
migrations. Profiles, goals, fitness planning, logging, AI inference, training,
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
to view your private account. Passwords must be 15–128 characters. Registration
does not automatically sign in. No real user data belongs in test fixtures.

For all 29 checks, including PostgreSQL integration, use the disposable runner:

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
  main.py                 Application composition and browser policies
  routes.py               Public page and health controllers
frontend/
  templates/index.html    English introduction and availability states
  static/css/styles.css   Responsive layout and visual system
tests/test_web.py         Web-shell and public-asset boundary checks
docs/
  architecture.md         Layer boundaries and staged implementation
  environment.md          Verified dependencies and hardware limitations
```

Account-input services, SQLAlchemy account/session models, migration files,
authentication controllers, and private account pages are now present. Fitness
services and AI/vision adapters will be introduced with their features.
See [database configuration](docs/database.md), [architecture](docs/architecture.md), [environment](docs/environment.md), and
[authentication](docs/authentication.md), and [development rules](AGENTS.md).

## Next milestone

Add private fitness profiles and goals, using the authenticated server-side identity. Metric units, user-selected IANA time zones, Monday week
boundaries, and customizable meal schedules are confirmed product defaults.
Use only synthetic data in tests; never commit real profiles or activity records.
