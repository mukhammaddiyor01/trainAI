"""Bounded same-origin authentication requests and server-derived identity."""

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from backend.accounts import (account_for_token, authenticate_account, create_login_session,
                              register_account, revoke_login_session)
from backend.session_tokens import SESSION_COOKIE, SESSION_SECONDS

router = APIRouter(prefix="/auth")
MAX_AUTH_BYTES = 2048


def require_same_origin(request: Request) -> None:
    if request.headers.get("origin") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Submit this request from the TrainAI page.")


async def read_credentials(request: Request) -> tuple[str, str]:
    require_same_origin(request)
    if request.headers.get("content-type", "").split(";", 1)[0].strip() != "application/json":
        raise HTTPException(415, "Send credentials as JSON.")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_AUTH_BYTES:
            raise HTTPException(413, "The sign-in request is too large.")
        content.extend(chunk)
    try:
        values = json.loads(content)
    except (ValueError, UnicodeError, RecursionError):
        raise HTTPException(422, "Check the username and password fields.") from None
    if not isinstance(values, dict) or set(values) != {"username", "password"}:
        raise HTTPException(422, "Provide only username and password.")
    username, password = values["username"], values["password"]
    if not isinstance(username, str) or not isinstance(password, str):
        raise HTTPException(422, "Username and password must be text.")
    if len(username) > 128 or len(password) > 128:
        raise HTTPException(422, "Check the username and password lengths.")
    # Reject escaped surrogate characters before they reach Argon2's UTF-8 encoder.
    try:
        password.encode("utf-8")
    except UnicodeError:
        raise HTTPException(422, "Use valid text for the password.") from None
    return username, password


async def auth_work(request: Request, function, *args):
    # Bound memory-intensive Argon2 operations and keep them off the event loop.
    slots = request.app.state.auth_slots
    if not slots.acquire(blocking=False):
        raise HTTPException(429, "Another sign-in is in progress. Try again shortly.")
    try:
        return await run_in_threadpool(function, *args)
    finally:
        slots.release()


@router.post("/register", status_code=201)
async def register(request: Request):
    username, password = await read_credentials(request)
    identity = await auth_work(request, register_account, username, password)
    return {"user_id": str(identity.user_id), "username": identity.username}


def sign_in(username: str, password: str, previous_token: str | None):
    identity = authenticate_account(username, password)
    return identity, create_login_session(identity, previous_token)


@router.post("/login")
async def login(request: Request):
    username, password = await read_credentials(request)
    identity, token = await auth_work(
        request, sign_in, username, password, request.cookies.get(SESSION_COOKIE)
    )
    response = JSONResponse({"user_id": str(identity.user_id), "username": identity.username})
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
        secure=request.url.scheme == "https", samesite="strict", path="/",
    )
    return response


@router.get("/me")
async def me(request: Request):
    identity = await run_in_threadpool(account_for_token, request.cookies.get(SESSION_COOKIE))
    if identity is None:
        raise HTTPException(401, "Sign in to continue.")
    return {"user_id": str(identity.user_id), "username": identity.username}


@router.post("/logout", status_code=204)
async def logout(request: Request):
    require_same_origin(request)
    await run_in_threadpool(revoke_login_session, request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict")
    return response
