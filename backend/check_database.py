"""Explicit read-only database connectivity check: python -m backend.check_database."""

from sqlalchemy.exc import SQLAlchemyError

from backend.config import DatabaseConfigurationError
from backend.database import check_database_connection, close_database


def main() -> int:
    try:
        check_database_connection()
    except DatabaseConfigurationError as error:
        print(str(error))
        return 1
    except SQLAlchemyError:
        print("PostgreSQL connection failed. Check local configuration and server availability.")
        return 1
    finally:
        close_database()
    print("PostgreSQL connection verified. No schema changes were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
