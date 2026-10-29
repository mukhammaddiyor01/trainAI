"""Sign-in pages and an account view resolved from the session cookie."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from backend.accounts import account_for_token
from backend.config import DatabaseConfigurationError
from backend.routes import templates
from backend.session_tokens import SESSION_COOKIE

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={
        "mode": "login", "created": request.query_params.get("created") == "1",
    })


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={
        "mode": "register", "created": False,
    })


@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    try:
        identity = await run_in_threadpool(account_for_token, request.cookies.get(SESSION_COOKIE))
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    if identity is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request=request, name="account.html", context={"identity": identity})
