# TrainAI

A fitness planning application for adults working toward weight gain, weight
loss, or weight maintenance. The intended workflow is:

**Profile → weekly plan → daily log → weekly review → approved plan revision.**

## Current status

The web foundation is implemented: an English responsive introduction page,
Jinja2 templates, local static assets, and a web-process health endpoint.
Accounts, profiles, PostgreSQL persistence, planning, logging, AI inference,
training, and camera tracking are not implemented in this milestone. The page
does not accept private fitness data or show fabricated progress.

## Local setup

Verified with Python 3.12 on Apple Silicon. Use an isolated environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt -c constraints.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Stop the server with Ctrl+C. Run commands from the
repository root. No database, credentials, model downloads, or camera permissions
are needed for the web shell.

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

Only layers currently needed have files. Plain Python services, SQLAlchemy models,
Alembic migrations, and AI/vision adapters will be added with their features.
See [database configuration](docs/database.md), [architecture](docs/architecture.md), [environment](docs/environment.md), and
[development rules](AGENTS.md).

## Next milestone

Add private accounts, server-side ownership checks, profiles, goals, and explicit
PostgreSQL migrations. Metric units, user-selected IANA time zones, Monday week
boundaries, and customizable meal schedules are confirmed product defaults.
Use only synthetic data in tests; never commit real profiles or activity records.
