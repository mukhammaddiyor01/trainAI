"""Plain account-input rules; identity and hashing remain outside this service."""

import re


class InvalidAccountInput(ValueError):
    """An account input does not meet the documented rules."""


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{3,32}", username):
        raise InvalidAccountInput("Use 3–32 letters, numbers, or underscores for your username.")
    return username


def validate_password(value: str) -> None:
    # Passwords are not trimmed or normalized; spaces and Unicode are allowed.
    if not 15 <= len(value) <= 128 or "\x00" in value:
        raise InvalidAccountInput("Use a password between 15 and 128 characters.")
