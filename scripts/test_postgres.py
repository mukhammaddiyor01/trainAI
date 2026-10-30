"""Test migrations and integration behavior in a temporary socket-only cluster.

Run with .venv/bin/python scripts/test_postgres.py. Requires local PostgreSQL
binaries. Never connects to the application's configured database.
"""

import argparse
import os
import secrets
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="Open a disposable browser-test server on port 8001")
    parser.add_argument("--pattern", default="test*.py", help="Explicit unittest file pattern for a small increment")
    arguments = parser.parse_args()
    serve = arguments.serve
    for name in ["initdb", "pg_ctl", "createdb"]:
        if not shutil.which(name):
            print("Install PostgreSQL binaries before running isolated database tests.")
            return 1
    root = Path(__file__).resolve().parent.parent
    temporary = tempfile.TemporaryDirectory(prefix="trainai-postgres-", dir="/private/tmp")
    directory = Path(temporary.name)
    data, socket = directory / "data", directory / "socket"
    socket.mkdir(mode=0o700)
    started = False
    try:
        run("initdb", "-D", str(data), "-U", "trainai_test", "--auth-local=trust",
            "--auth-host=reject", "--encoding=UTF8", "--no-locale", stdout=subprocess.DEVNULL)
        run("pg_ctl", "-D", str(data), "-l", str(directory / "server.log"),
            "-o", f"-k {socket} -p 55439 -c listen_addresses=''", "-w", "start",
            stdout=subprocess.DEVNULL)
        started = True
        run("createdb", "-h", str(socket), "-p", "55439", "-U", "trainai_test", "trainai_test")
        from sqlalchemy.engine import URL
        url = URL.create("postgresql+psycopg", username="trainai_test", database="trainai_test",
                         query={"host": str(socket), "port": "55439"}).render_as_string(hide_password=False)
        from sqlalchemy import create_engine, text
        engine = create_engine(url)
        try:
            with engine.connect() as connection:
                actual = connection.execute(text(
                    "SELECT current_database(), current_user, current_setting('unix_socket_directories')"
                )).one()
                if tuple(actual) != ("trainai_test", "trainai_test", str(socket)):
                    raise RuntimeError("Refusing migrations outside the owned temporary cluster.")
        finally:
            engine.dispose()
        environment = {**os.environ, "DATABASE_URL": url, "TRAINAI_TEST_DATABASE_URL": url,
                       "TRAINAI_COOKIE_NAME": "trainai_test_" + secrets.token_hex(6)}
        run(sys.executable, "-m", "alembic", "upgrade", "head", cwd=root, env=environment)
        if serve:
            print("Disposable browser test: http://127.0.0.1:8001 (Ctrl+C stops and removes test data).", flush=True)
            try:
                run(sys.executable, "-m", "backend", "--port", "8001", cwd=root, env=environment)
            except KeyboardInterrupt:
                pass
        else:
            run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", arguments.pattern, "-v", cwd=root, env=environment)
            run(sys.executable, "-m", "alembic", "downgrade", "base", cwd=root, env=environment)
            run(sys.executable, "-m", "alembic", "upgrade", "head", cwd=root, env=environment)
    finally:
        if started:
            run("pg_ctl", "-D", str(data), "-m", "fast", "-w", "stop", stdout=subprocess.DEVNULL)
        temporary.cleanup()
    print("Isolated PostgreSQL checks passed; temporary cluster removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
