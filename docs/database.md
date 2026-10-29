# PostgreSQL Configuration

Persistence uses PostgreSQL, SQLAlchemy 2.1, and psycopg 3. No SQLite fallback is
provided. Database URLs, passwords, and private data must never be committed.

Set `DATABASE_URL` in the environment or in an ignored `.env` at the project root.
Use the `postgresql+psycopg` driver and an explicit database name. The committed
`.env.example` contains only an empty placeholder. Environment values take
precedence; an empty environment value is an error rather than a silent fallback.
Restart the web process after changing database configuration.

Run the explicit, read-only connectivity check:

```bash
.venv/bin/python -m backend.check_database
```

The command runs SELECT 1, returns a nonzero exit status on failure, and reports
generic messages without connection details. It never creates a database or tables.
The public web shell remains usable without database configuration. Web health
does not imply persistence or model readiness.

The application shares an Engine pool, never mutable Sessions. Each
`session_scope()` commits on success, rolls back on error, and closes its Session.
Engine creation is lazy; imports and app startup never create schema or connect.
Alembic migrations and account tables arrive in the next small increment.

Verified dependencies: SQLAlchemy 2.1.6, psycopg/psycopg-binary 3.3.6, and
python-dotenv 1.2.4. See constraints.txt for the exact resolved dependency set.

Sources: [SQLAlchemy sessions](https://docs.sqlalchemy.org/en/21/orm/session_basics.html),
[psycopg dialect](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg),
[psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).
