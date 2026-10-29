"""Sign-in pages and an account view resolved from the session cookie."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from backend.guards import optional_account
from backend.profiles import read_profile
from starlette.concurrency import run_in_threadpool
from backend.config import DatabaseConfigurationError
from backend.routes import templates

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
        identity = await optional_account(request)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    if identity is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request=request, name="account.html", context={"identity": identity})


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        details = await run_in_threadpool(read_profile, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="profile.html", context={"profile": details})
