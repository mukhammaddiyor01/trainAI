"""HTTP metadata bounds and bounded JSON API responses for the local server."""

from starlette.responses import JSONResponse

from backend.rate_limits import AttemptLimiter

MAX_HEADER_BYTES = 16 * 1024
MAX_HEADER_COUNT = 64
MAX_TARGET_BYTES = 4096
MAX_API_RESPONSE_BYTES = 64 * 1024


class HttpLimitsMiddleware:
    def __init__(self, app):
        self.app = app
        self.api_attempts = AttemptLimiter()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = scope.get("headers", [])
        header_bytes = sum(len(key) + len(value) for key, value in headers)
        if len(headers) > MAX_HEADER_COUNT or header_bytes > MAX_HEADER_BYTES:
            return await JSONResponse({"detail": "Request headers are too large."}, 431)(scope, receive, send)
        target_size = len(scope.get("raw_path") or scope["path"].encode("utf-8")) + len(scope.get("query_string", b""))
        if target_size > MAX_TARGET_BYTES:
            return await JSONResponse({"detail": "The request URL is too long."}, 414)(scope, receive, send)
        if any(key.lower() == b"forwarded" or key.lower().startswith(b"x-forwarded-")
               for key, value in headers):
            return await JSONResponse({"detail": "Proxy headers are not accepted by this local server."}, 400)(scope, receive, send)

        if not scope["path"].startswith(("/auth/", "/api/")):
            return await self.app(scope, receive, send)
        peer = (scope.get("client") or ("unknown", 0))[0]
        retry_after = self.api_attempts.check("api-peer", peer, 120)
        if retry_after:
            return await JSONResponse({"detail": "Too many API requests. Try again shortly."}, 429,
                                      headers={"Retry-After": str(retry_after)})(scope, receive, send)
        response_start = None
        buffered = bytearray()
        blocked = False

        async def limited_send(message):
            nonlocal response_start, blocked
            if blocked:
                return
            if message["type"] == "http.response.start":
                content_type = dict(message.get("headers", [])).get(b"content-type", b"")
                if content_type.split(b";", 1)[0].lower() == b"application/json":
                    response_start = message
                    return
            if message["type"] == "http.response.body" and response_start is not None:
                chunk = message.get("body", b"")
                if len(buffered) + len(chunk) > MAX_API_RESPONSE_BYTES:
                    blocked = True
                    buffered.clear()
                    return await JSONResponse({"detail": "The response could not be completed."}, 500)(scope, receive, send)
                buffered.extend(chunk)
                if not message.get("more_body", False):
                    await send(response_start)
                    await send({"type": "http.response.body", "body": bytes(buffered)})
                    response_start = None
                return
            await send(message)

        await self.app(scope, receive, limited_send)
