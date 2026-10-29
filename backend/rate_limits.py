"""Bounded rolling-window limits for a single local application process."""

from collections import deque
import hashlib
import math
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request

AUTH_WINDOW_SECONDS = 60
AUTH_PEER_ATTEMPTS = 30
LOGIN_ACCOUNT_ATTEMPTS = 8
MAX_LIMIT_BUCKETS = 4096


class AttemptLimiter:
    def __init__(self, clock=monotonic, max_buckets=MAX_LIMIT_BUCKETS):
        self.clock = clock
        self.max_buckets = max_buckets
        self.buckets: dict[tuple[str, str], deque] = {}
        self.lock = Lock()

    def check(self, scope: str, value: str, limit: int) -> int:
        # Keep bounded fingerprints, not raw usernames or client addresses.
        key = (scope, hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest())
        now = self.clock()
        cutoff = now - AUTH_WINDOW_SECONDS
        with self.lock:
            for existing_key, events in list(self.buckets.items()):
                while events and events[0] <= cutoff:
                    events.popleft()
                if not events:
                    del self.buckets[existing_key]
            events = self.buckets.get(key)
            if events is None:
                if len(self.buckets) >= self.max_buckets:
                    return AUTH_WINDOW_SECONDS
                events = self.buckets[key] = deque()
            if len(events) >= limit:
                return max(1, math.ceil(events[0] + AUTH_WINDOW_SECONDS - now))
            events.append(now)
        return 0


def enforce_attempt_limit(request: Request, scope: str, value: str, limit: int) -> None:
    retry_after = request.app.state.auth_attempts.check(scope, value, limit)
    if retry_after:
        raise HTTPException(429, "Too many attempts. Try again shortly.",
                            headers={"Retry-After": str(retry_after)})
