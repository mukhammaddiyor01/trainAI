# Architecture and Implementation Plan

## Application boundaries

The application uses MVC with explicit service and adapter boundaries:

| Responsibility | Location | Boundary |
| --- | --- | --- |
| Composition | backend/main.py | Construct app and connect routes/assets |
| Controllers | backend/routes.py and feature route modules | Validate HTTP input and coordinate work |
| Views | frontend/templates and frontend/static | Display real state and collect user input |
| Persistence | backend/models.py and backend/database.py | SQLAlchemy tables and short-lived transactions |
| Services (as needed) | backend/services | Plain Python calculations and business rules |
| Adapters (later) | backend/adapters | Models, tokenizers, datasets, and vision libraries |

Controllers convert persistence results into plain Python values before calling
services. No ORM objects, HTTP exceptions, or model-library tensors enter business
services. Model output is untrusted until schema and business validation pass.
No repository interfaces, containers, or speculative empty layers are needed.

## Persistence decision

Use PostgreSQL with SQLAlchemy and psycopg, managed through reviewed Alembic
migrations. This follows the reference project's explicit transaction lifecycle
and supports ownership foreign keys, atomic approvals, and a partial unique index
for one active plan per user. Never silently replace it with SQLite. Database
configuration is required for private account/profile/goal operations; the public
shell can still open without it.
No database is created or contacted at startup in this milestone.

Reference: [SQLAlchemy PostgreSQL/psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg).

## Implementation sequence

1. Web shell, verified environment, and honest availability states (completed foundation).
2. Authentication, private profiles/goals, PostgreSQL setup and migrations.
3. Small sourced exercise and food catalogs, with reviewed IDs and units.
4. Deterministic workout/nutrition planning with documented calculation methods.
5. Daily records separating planned actions, actual actions, and missing data.
6. Weekly analysis and transactional, idempotent plan approval/versioning.
7. Tokenizer and local TinyLlama baseline with strict input/output limits.
8. Licensed dataset preparation, LoRA/SFT, and held-out baseline comparisons.
9. Local OpenCV/pose integration and user-confirmed repetition logging.
10. Synthetic end-to-end product verification and complete documentation.

Each increment is verified and committed separately. Authentication is implemented
before collecting private multi-user data. Initial setup is shared by master and
develop; subsequent work stays on develop. Deployment and paid training are outside
the authorized scope.

## AI and camera choices

TinyLlama/TinyLlama-1.1B-Chat-v1.0 is a candidate for the English baseline, not an
authority for nutrition or medical facts. Pin a revision and verify actual device,
dtype, context handling, and output validity at integration time. Training and
inference are separate from web-server startup.

DeepSeek-V4.1-Flash-1017 is a later provider/comparison option. The model page checked
on 2026-10-29 lists 763B parameters; full local weights are unsuitable for the
observed 16 GB machine. Its prompt encoding differs from a standard Jinja chat
template. No weights are downloaded and no private data is sent to a hosted model.

Sources: [TinyLlama model card](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0),
[DeepSeek model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017).

Camera integration follows the core planning MVP. OpenCV needs a separate pose
model for landmarks; its license and measured performance must be checked before
selection. Repetition rules remain in plain Python and camera results require
confirmation before persistence.
