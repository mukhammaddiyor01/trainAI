"""Opaque session tokens; only their SHA-256 digests belong in persistence."""

import hashlib
import re
import secrets

SESSION_SECONDS = 24 * 60 * 60
SESSION_COOKIE = "trainai_session"


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str | None) -> str | None:
    if token is None or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return None
    return hashlib.sha256(token.encode("ascii")).hexdigest()
