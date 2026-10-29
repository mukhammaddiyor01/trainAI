"""Limit failures must not expose partial private data or trust proxy spoofing."""

import asyncio
import unittest
from unittest.mock import patch

import anyio
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from starlette.requests import Request

from backend.http_limits import MAX_API_RESPONSE_BYTES
from backend.main import create_app
from backend.request_validation import read_bounded_body


class HttpLimitTests(unittest.TestCase):
    def test_proxy_headers_large_headers_and_long_urls_are_rejected(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            for name in ["Forwarded", "X-Forwarded-For", "X-Forwarded-Proto"]:
                self.assertEqual(client.get("/health", headers={name: "forged"}).status_code, 400)
            self.assertEqual(client.get("/health", headers={"X-Large": "x" * 17000}).status_code, 431)
            self.assertEqual(client.get("/health?" + "x" * 4100).status_code, 414)

    def test_streaming_json_limit_does_not_leak_the_first_chunk(self):
        app = create_app()

        @app.get("/api/oversized-test")
        def oversized():
            def chunks():
                yield b'"private-prefix'
                yield b"x" * MAX_API_RESPONSE_BYTES
            return StreamingResponse(chunks(), media_type="application/json")

        with TestClient(app, base_url="http://127.0.0.1") as client:
            response = client.get("/api/oversized-test")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-prefix", response.text)
        self.assertLess(len(response.content), 200)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_chunked_body_limit_works_without_content_length(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            response = client.post("/auth/login", headers={"origin": "http://127.0.0.1", "content-type": "application/json"},
                                   content=iter([b"x" * 1024, b"x" * 1025]))
        self.assertEqual(response.status_code, 413)

    def test_slow_body_expires_and_invalid_length_fails_before_read(self):
        async def slow_receive():
            await anyio.sleep_forever()

        scope = {"type": "http", "headers": []}
        with patch("backend.request_validation.BODY_TIMEOUT_SECONDS", 0.01):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(read_bounded_body(Request(scope, slow_receive), 100))
            self.assertEqual(error.exception.status_code, 408)
        scope["headers"] = [(b"content-length", b"invalid")]
        with self.assertRaises(HTTPException) as error:
            asyncio.run(read_bounded_body(Request(scope, slow_receive), 100))
        self.assertEqual(error.exception.status_code, 400)


    def test_api_request_rate_limit_preserves_health_access(self):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            for attempt in range(120):
                self.assertEqual(client.get("/auth/me").status_code, 401)
            response = client.get("/auth/me")
            self.assertEqual(response.status_code, 429)
            self.assertIn("retry-after", response.headers)
            self.assertEqual(client.get("/health").status_code, 200)

    def test_invalid_response_schema_is_sanitized(self):
        from backend.schemas import AccountResponse
        app = create_app()

        @app.get("/api/invalid-response-test", response_model=AccountResponse)
        def invalid_response():
            return {"password_hash": "private-response-value"}

        with TestClient(app, base_url="http://127.0.0.1") as client:
            response = client.get("/api/invalid-response-test")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-response-value", response.text)
