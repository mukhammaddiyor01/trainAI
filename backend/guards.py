"""Reusable FastAPI guards; browser-supplied identifiers never establish identity."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from backend.accounts import AccountIdentity, account_for_token
from backend.session_tokens import SESSION_COOKIE


def require_same_origin(request: Request) -> None:
    if request.headers.get("origin") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Submit this request from the TrainAI page.")


async def optional_account(request: Request) -> AccountIdentity | None:
    return await run_in_threadpool(account_for_token, request.cookies.get(SESSION_COOKIE))


async def require_account(
    identity: Annotated[AccountIdentity | None, Depends(optional_account)],
) -> AccountIdentity:
    if identity is None:
        raise HTTPException(401, "Sign in to continue.")
    return identity


AuthenticatedAccount = Annotated[AccountIdentity, Depends(require_account)]
