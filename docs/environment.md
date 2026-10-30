# Verified Development Environment

Checked on 2026-10-29. TrainAI uses its own Python 3.12 virtual environment;
reference-project environments are not reused or changed.

## Runtime and dependencies

| Component | Installed and checked |
| --- | --- |
| Python | 3.12.14, arm64 |
| FastAPI | 0.162.0 |
| Uvicorn | 0.54.0 |
| Jinja2 | 3.1.6 |
| Starlette (resolved dependency) | 1.10.0 |
| Pydantic (resolved dependency) | 2.14.1 |
| HTTPX2 (test dependency) | 2.16.0 |

`requirements.txt` pins direct runtime dependencies; `requirements-dev.txt` adds
the HTTP test client. `constraints.txt` records all resolved application/test
dependencies from the isolated environment. Install with `-c constraints.txt` to
reproduce this resolution. `pip check` reported no broken requirements, and the
seven web-shell tests passed with these versions.

Official sources checked before installation:
- [FastAPI version guidance](https://fastapi.tiangolo.com/deployment/versions/)
- [FastAPI template integration](https://fastapi.tiangolo.com/advanced/templates/)
- [Starlette TestClient](https://starlette.dev/testclient/) (uses HTTPX2)
- [FastAPI package metadata](https://pypi.org/pypi/fastapi/0.162.0/json)
- [Uvicorn package metadata](https://pypi.org/pypi/uvicorn/0.54.0/json)
- [Jinja2 package metadata](https://pypi.org/pypi/jinja2/3.1.6/json)
- [HTTPX2 package metadata](https://pypi.org/pypi/httpx2/2.16.0/json)

The registry metadata supports Python 3.12 for this combination. Do not manually
upgrade Starlette or Pydantic independently without rerunning compatibility checks.
The OpenTelemetry API is a transitive FastAPI dependency; this application does
not configure a telemetry SDK or exporter.

## Hardware and later ML work

Initial machine inspection found an Apple M2 Pro, 16 GB unified memory, a 10-core
CPU, and a 16-core Metal-capable GPU. An existing reference environment reported
PyTorch 2.14.1 with CUDA unavailable, MPS compiled in, and MPS unavailable in that
probe. This is not proof that Metal inference cannot work; repeat the check in
TrainAI's own environment at the ML milestone, including a real tensor operation.

PyTorch, Transformers, tokenizers, datasets, PEFT, TRL, and OpenCV are deliberately
not installed yet. No TrainAI ML inference or training has been verified. CUDA-only
training settings must not be assumed to work on Apple Silicon.

The PostgreSQL client was 16.15 during initial inspection; 127.0.0.1:5432 returned
no response. That observation does not establish server absence. PostgreSQL
connection credentials and a dedicated database will be configured explicitly in
the next milestone. No database was created, started, migrated, or substituted.

## Persistence and authentication increment

The isolated environment now also includes SQLAlchemy 2.1.6, psycopg and
psycopg-binary 3.3.6, python-dotenv 1.2.4, Alembic 1.20.1, and argon2-cffi 25.1.0.
The exact transitive dependency versions are recorded in constraints.txt. PyPI
metadata and the official SQLAlchemy, psycopg, Alembic, and argon2-cffi documentation
were checked before installation. All 29 tests passed in the isolated PostgreSQL
runner, with no skipped tests.

A subsequent unrestricted connectivity check confirmed the local PostgreSQL server
accepts connections. The user supplied a DATABASE_URL through the ignored .env.
SELECT 1 passed, the selected database had no existing tables, and account migration
0001 was applied explicitly. No credentials or database address are recorded here.

## Security/profile verification

Pydantic 2.14.1 and AnyIO 4.15.1 are now explicit direct dependencies, already
present in the recorded compatible resolution. No extra runtime packages were
needed for the security or profile increment. All 53 isolated checks passed.
The configured database was explicitly upgraded to revision 0002 after revision
and conflict checks. PyPA pip-audit 2.10.1 reported no known advisories across all
29 pinned packages on 2026-10-29. See docs/security.md for scope and limitations.

## Goal verification — 2026-10-30

No new dependencies were installed. All 68 working-tree tests passed in disposable
PostgreSQL after the user selected the shared 8-character password minimum. The
configured database was explicitly upgraded to 0003 after revision/conflict checks.
Goal browser checks used synthetic data only. The 2026-10-29 dependency-advisory
snapshot remains historical and was not rerun for these dependency-free changes.
