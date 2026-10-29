"""Explicit migrations share application configuration without logging secrets."""

from alembic import context

from backend.config import get_database_url
from backend.database import Base, create_database_engine
from backend import models  # Register ORM metadata for schema comparisons.


def run_offline() -> None:
    context.configure(
        url=get_database_url(), target_metadata=Base.metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"}, compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    engine = create_database_engine()
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_offline()
else:
    run_online()
