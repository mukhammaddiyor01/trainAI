"""Opaque session tokens; only their SHA-256 digests belong in persistence."""

import hashlib
import os
import re
import secrets

SESSION_SECONDS = 24 * 60 * 60

def session_cookie_name() -> str:
    name = os.environ.get("TRAINAI_COOKIE_NAME", "trainai_session")
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,47}", name):
        raise ValueError("TRAINAI_COOKIE_NAME must be a valid lowercase cookie name.")
    return name


SESSION_COOKIE = session_cookie_name()


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str | None) -> str | None:
    if token is None or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return None
    return hashlib.sha256(token.encode("ascii")).hexdigest()
