"""Account persistence and server-side identity; no ORM records escape this module."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from backend.database import session_scope
from backend.models import LoginSession, User
from backend.passwords import hash_password, hasher, verify_password
from backend.services.accounts import InvalidAccountInput, normalize_username
from backend.session_tokens import SESSION_SECONDS, new_session_token, token_digest


class UsernameUnavailable(ValueError):
    """An account with this normalized username already exists."""


class InvalidCredentials(ValueError):
    """The supplied username and password do not identify an account."""


@dataclass(frozen=True)
class AccountIdentity:
    user_id: UUID
    username: str


@lru_cache(maxsize=1)
def dummy_hash() -> str:
    # Unknown usernames still take the Argon2 verification path.
    return hash_password(new_session_token())


def register_account(username: str, password: str) -> AccountIdentity:
    username = normalize_username(username)
    password_hash = hash_password(password)
    try:
        with session_scope() as session:
            user = User(username=username, password_hash=password_hash)
            session.add(user)
            session.flush()
            identity = AccountIdentity(user.id, user.username)
    except IntegrityError as error:
        if getattr(getattr(error.orig, "diag", None), "constraint_name", None) == "users_username_key":
            raise UsernameUnavailable("That username is already in use.") from None
        raise
    return identity


def authenticate_account(username: str, password: str) -> AccountIdentity:
    try:
        username = normalize_username(username)
    except InvalidAccountInput:
        raise InvalidCredentials("Username or password is incorrect.") from None
    with session_scope() as session:
        row = session.execute(select(User.id, User.username, User.password_hash).where(
            User.username == username
        )).one_or_none()
    password_hash = row.password_hash if row else dummy_hash()
    valid = verify_password(password_hash, password)
    if row is None or not valid:
        raise InvalidCredentials("Username or password is incorrect.")
    if hasher.check_needs_rehash(password_hash):
        replacement = hash_password(password)
        with session_scope() as session:
            session.execute(update(User).where(User.id == row.id, User.password_hash == password_hash)
                            .values(password_hash=replacement))
    return AccountIdentity(row.id, row.username)


def create_login_session(identity: AccountIdentity, previous_token: str | None = None) -> str:
    token = new_session_token()
    now = datetime.now(timezone.utc)
    with session_scope() as session:
        previous_digest = token_digest(previous_token)
        if previous_digest:
            session.execute(delete(LoginSession).where(LoginSession.token_digest == previous_digest))
        session.add(LoginSession(
            token_digest=token_digest(token), user_id=identity.user_id, created_at=now,
            expires_at=now + timedelta(seconds=SESSION_SECONDS),
        ))
    return token


def account_for_token(token: str | None) -> AccountIdentity | None:
    digest = token_digest(token)
    if digest is None:
        return None
    with session_scope() as session:
        row = session.execute(select(User.id, User.username).join(
            LoginSession, LoginSession.user_id == User.id
        ).where(LoginSession.token_digest == digest,
                LoginSession.expires_at > datetime.now(timezone.utc))).one_or_none()
        return AccountIdentity(row.id, row.username) if row else None


def revoke_login_session(token: str | None) -> None:
    digest = token_digest(token)
    if digest is not None:
        with session_scope() as session:
            session.execute(delete(LoginSession).where(LoginSession.token_digest == digest))
