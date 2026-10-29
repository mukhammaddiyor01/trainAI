"""Reject unsafe configuration without connecting or leaking credentials."""

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.check_database import main
from backend.config import DatabaseConfigurationError, get_database_url
from backend.main import create_app


class DatabaseConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("backend.config.dotenv_values", return_value={}))
        self.enterContext(patch.dict(os.environ, {}, clear=True))

    def test_missing_and_unsupported_database_are_rejected(self):
        for value in ["", "sqlite:///private.db", "postgresql://localhost/test",
                      "postgresql+psycopg://localhost", "not a URL"]:
            with self.subTest(value=value), patch.dict(os.environ, {"DATABASE_URL": value}):
                with self.assertRaises(DatabaseConfigurationError):
                    get_database_url()

    def test_environment_precedes_local_file(self):
        with patch("backend.config.dotenv_values", return_value={"DATABASE_URL": "invalid"}):
            with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg://localhost/test"}):
                self.assertEqual(get_database_url().database, "test")
            with patch.dict(os.environ, {"DATABASE_URL": ""}):
                with self.assertRaises(DatabaseConfigurationError):
                    get_database_url()

    def test_local_file_is_read_only_when_environment_is_absent(self):
        with patch("backend.config.dotenv_values", return_value={
            "DATABASE_URL": "postgresql+psycopg://localhost/test"
        }):
            self.assertEqual(get_database_url().database, "test")

    def test_invalid_configuration_does_not_print_credentials(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"DATABASE_URL": "invalid://user:private-value@host/test"}):
            with redirect_stdout(output):
                self.assertEqual(main(), 1)
        self.assertNotIn("private-value", output.getvalue())

    def test_web_shell_starts_without_database_configuration_or_connections(self):
        with patch("backend.database.create_engine", side_effect=AssertionError("Unexpected DB access")):
            with TestClient(create_app(), base_url="http://127.0.0.1") as client:
                self.assertEqual(client.get("/").status_code, 200)
                self.assertEqual(client.get("/health").json()["scope"], "web")


if __name__ == "__main__":
    unittest.main()
