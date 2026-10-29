"""Argon2id hashing; plaintext passwords are never persisted."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from backend.services.accounts import InvalidAccountInput, validate_password

hasher = PasswordHasher()


def hash_password(password: str) -> str:
    validate_password(password)
    return hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        validate_password(password)
    except InvalidAccountInput:
        return False
    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False
