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
The account migration adds users and server-side sessions. Only token digests are
stored; raw session tokens must never be persisted.

Verified dependencies: SQLAlchemy 2.1.6, psycopg/psycopg-binary 3.3.6, and
python-dotenv 1.2.4. See constraints.txt for the exact resolved dependency set.

Sources: [SQLAlchemy sessions](https://docs.sqlalchemy.org/en/21/orm/session_basics.html),
[psycopg dialect](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg),
[psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).

## Explicit migrations

After configuring an approved dedicated database, run:

```bash
.venv/bin/python -m alembic upgrade head
```

This is an explicit operator action, never a web-startup operation. Downgrades
remove data and are not authorized against a real user database.

## Isolated integration checks

```bash
.venv/bin/python scripts/test_postgres.py
```

The runner creates a fresh temporary PostgreSQL cluster, accessible only through
a Unix socket inside a private temporary directory. It uses synthetic users,
checks migration/model parity, commits, rollbacks, unique constraints, and foreign
keys, then checks downgrade/upgrade and removes only its own cluster. It never
uses DATABASE_URL from the application configuration. Requires installed initdb,
pg_ctl, and createdb. Direct integration test discovery is skipped unless an
explicit TRAINAI_TEST_DATABASE_URL ending in _test matches DATABASE_URL.

## Operation budgets

The runtime pool is capped at 5 pooled plus 5 overflow connections, with a
3-second pool checkout timeout. Connections and SQL statements have 5-second
bounds; lock waits are capped at 2 seconds. Integration checks confirm the
PostgreSQL statement_timeout and lock_timeout settings are active. Slow queries
and pool failures become generic persistence errors, without leaking parameters.
Large future administrative migrations may need an explicit reviewed operator
configuration; never remove runtime bounds silently.

For a single independently developed increment, an explicit test pattern is
available, for example `scripts/test_postgres.py --pattern test_profile_storage.py`.
The default still discovers the full suite. A targeted result is not a full-suite
result and must be reported as such. Both modes use the isolated cluster and
perform migration round trips.


## Training-preference migration — 2026-10-31

Migration 0004 adds training_preferences with one row per saved profile and
bounded SQL choices/selection sets. It was tested through isolated upgrade,
downgrade, and upgrade, with migration/model parity checks. After confirming
revision 0003 and no table conflict, the configured database was explicitly
upgraded to 0004. Existing tables were not modified; no synthetic records were
written to the configured database. See [training preferences](training-preferences.md).


## Food-preference migration — 2026-10-31

Migration 0005 adds food_preferences with one owner-keyed row per basic profile.
SQL bounds cover choices, preparation, arrays, and explicit allergy-state/list
consistency. Disposable upgrade/downgrade/upgrade and metadata parity passed.
After checking revision 0004 and no food_preferences table conflict, the configured
database was explicitly upgraded to 0005. Existing tables were not modified and
no synthetic records were written there. See [food preferences](food-preferences.md).


## Energy-preference migration — 2026-11-02

Migration 0006 creates energy_preferences only, with one cascading owner foreign
key per profile and three explicit non-null choice columns. It performs no
backfill and stores no estimate or target. Atomic full-row upserts and all 75
valid choice combinations were tested in disposable PostgreSQL, alongside owner
isolation, concurrent complete selections, SQL bounds, cascade, and metadata parity.
The full 158-test suite and disposable migration round trips passed.

After verifying configured revision 0005 and no energy_preferences table conflict,
the reviewed additive migration was explicitly applied. Current configured and
expected revision: 0006. Existing tables/records were not modified; no synthetic
accounts or preferences were written to the configured database.

## Pending calorie proposal migration — 2026-11-05

Migration 0007 adds only `calorie_proposals`: server-generated IDs, owner foreign
keys, pending-only status, exact calculation source snapshots, unrounded results,
and pinned versions. It has no defaults/backfill for existing users. Disposable
PostgreSQL upgrade/downgrade/upgrade, metadata parity, and SQL constraint tests
passed with the complete 181-test suite. The configured database was checked at
0006 with no table conflict, then explicitly upgraded to 0007. No real user
rows were read or written. Approval and active-plan tables were not present at
this historical checkpoint.

## Calorie target migration — 2026-11-06

Migration 0008 adds approval lifecycle columns to proposals and a private
`calorie_target_versions` table. SQL constraints enforce unique owner/version,
one target per proposal, and a partial unique index for one active target per
owner. A proposal records the active version seen at creation. The migration
has no user-data backfill and does not activate existing pending proposals.
The full 196-test disposable suite passed, including downgrade/upgrade and
model parity. The configured database was checked at 0007 with no target table,
then upgraded to 0008. Only schema metadata was inspected; no user rows or
secrets were printed. A downgrade on the configured database remains unauthorized.

## Movement limitation migration — 2026-11-06

Migration 0009 creates `movement_limitations` with one non-null, SQL-constrained
status per profile and a cascading owner foreign key. It does not change
existing profile/training rows, infer an answer, or backfill users. The complete
206-test disposable suite passed, including migration downgrade/upgrade and
model parity. The configured database was at 0008 with no table conflict before
the additive upgrade; revision 0009 and exactly the new `user_id`/`status`
columns were confirmed afterward through schema metadata only.
