"""Bounded same-origin authentication requests and server-derived identity."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import ValidationError

from backend.request_validation import read_json
from backend.schemas import AccountResponse, Credentials
from starlette.concurrency import run_in_threadpool

from backend.accounts import (account_for_token, authenticate_account, create_login_session,
                              register_account, revoke_login_session)
from backend.session_tokens import SESSION_COOKIE, SESSION_SECONDS

router = APIRouter(prefix="/auth")
MAX_AUTH_BYTES = 2048


def require_same_origin(request: Request) -> None:
    if request.headers.get("origin") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Submit this request from the TrainAI page.")


async def read_credentials(request: Request) -> Credentials:
    require_same_origin(request)
    values = await read_json(request, MAX_AUTH_BYTES)
    try:
        return Credentials.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the username and password fields.") from None


async def auth_work(request: Request, function, *args):
    # Bound memory-intensive Argon2 operations and keep them off the event loop.
    slots = request.app.state.auth_slots
    if not slots.acquire(blocking=False):
        raise HTTPException(429, "Another sign-in is in progress. Try again shortly.")
    try:
        return await run_in_threadpool(function, *args)
    finally:
        slots.release()


@router.post("/register", status_code=201, response_model=AccountResponse)
async def register(request: Request, credentials: Annotated[Credentials, Depends(read_credentials)]):
    identity = await auth_work(request, register_account, credentials.username, credentials.password.get_secret_value())
    return AccountResponse(user_id=identity.user_id, username=identity.username)


def sign_in(username: str, password: str, previous_token: str | None):
    identity = authenticate_account(username, password)
    return identity, create_login_session(identity, previous_token)


@router.post("/login", response_model=AccountResponse)
async def login(request: Request, response: Response, credentials: Annotated[Credentials, Depends(read_credentials)]):
    identity, token = await auth_work(
        request, sign_in, credentials.username, credentials.password.get_secret_value(), request.cookies.get(SESSION_COOKIE)
    )
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
        secure=request.url.scheme == "https", samesite="strict", path="/",
    )
    return AccountResponse(user_id=identity.user_id, username=identity.username)


@router.get("/me", response_model=AccountResponse)
async def me(request: Request):
    identity = await run_in_threadpool(account_for_token, request.cookies.get(SESSION_COOKIE))
    if identity is None:
        raise HTTPException(401, "Sign in to continue.")
    return AccountResponse(user_id=identity.user_id, username=identity.username)


@router.post("/logout", status_code=204)
async def logout(request: Request):
    require_same_origin(request)
    await run_in_threadpool(revoke_login_session, request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict")
    return response
