"""Lazy PostgreSQL engine and isolated transaction sessions."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

from backend.config import get_database_url


class Base(DeclarativeBase):
    """Shared metadata for ORM records and explicit Alembic migrations."""


def create_database_engine() -> Engine:
    return create_engine(
        get_database_url(), pool_pre_ping=True, hide_parameters=True,
        pool_size=5, max_overflow=5, pool_timeout=3,
        connect_args={"connect_timeout": 5, "application_name": "trainai",
                      "options": "-c statement_timeout=5000 -c lock_timeout=2000"},
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_database_engine()


@contextmanager
def session_scope() -> Iterator[Session]:
    # Share the pool; each operation gets its own short-lived transaction.
    with Session(get_engine()) as session:
        with session.begin():
            yield session


def close_database() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()


def check_database_connection() -> None:
    with session_scope() as session:
        session.execute(text("SELECT 1"))
