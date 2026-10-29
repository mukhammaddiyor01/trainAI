"""Read explicit PostgreSQL configuration without exposing connection details."""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DatabaseConfigurationError(ValueError):
    """The application has no usable explicit PostgreSQL configuration."""


def get_database_url() -> URL:
    # Environment values take precedence, including an explicitly empty value.
    value = os.environ.get("DATABASE_URL")
    if value is None:
        value = dotenv_values(PROJECT_ROOT / ".env", interpolate=False).get("DATABASE_URL")
    if not value or not value.strip():
        raise DatabaseConfigurationError("Set DATABASE_URL before using persistence.")
    try:
        url = make_url(value)
    except (ArgumentError, ValueError):
        raise DatabaseConfigurationError("DATABASE_URL is not a valid PostgreSQL URL.") from None
    if url.drivername != "postgresql+psycopg" or not url.database:
        raise DatabaseConfigurationError(
            "DATABASE_URL must select postgresql+psycopg and an explicit database."
        )
    return url
