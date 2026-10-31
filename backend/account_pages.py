"""Sign-in pages and an account view resolved from the session cookie."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from backend.guards import optional_account
from backend.profiles import read_profile
from backend.goals import read_goal
from backend.training_preferences import read_training_preferences
from backend.services.training_preferences import MIN_SESSION_MINUTES, MAX_SESSION_MINUTES
from backend.services.accounts import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from starlette.concurrency import run_in_threadpool
from backend.config import DatabaseConfigurationError
from backend.routes import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={
        "mode": "login", "created": request.query_params.get("created") == "1",
        "min_password_length": MIN_PASSWORD_LENGTH, "max_password_length": MAX_PASSWORD_LENGTH,
    })


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={
        "mode": "register", "created": False,
        "min_password_length": MIN_PASSWORD_LENGTH, "max_password_length": MAX_PASSWORD_LENGTH,
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


@router.get("/goal", response_class=HTMLResponse)
async def goal_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        goal = await run_in_threadpool(read_goal, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="goal.html", context={
        "profile": profile, "goal": goal, "saved": request.query_params.get("saved") == "1",
    })


@router.get("/training-preferences", response_class=HTMLResponse)
async def training_preferences_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        preferences = await run_in_threadpool(read_training_preferences, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="training-preferences.html", context={
        "preferences": preferences, "saved": preferences is not None and request.query_params.get("saved") == "1",
        "min_session_minutes": MIN_SESSION_MINUTES, "max_session_minutes": MAX_SESSION_MINUTES,
    })
