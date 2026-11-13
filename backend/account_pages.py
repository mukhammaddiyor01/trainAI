"""Sign-in pages and an account view resolved from the session cookie."""

from fastapi import APIRouter, Request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from uuid import UUID
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from backend.guards import optional_account
from backend.profiles import read_profile
from backend.weight_entries import list_recent_weight_entries, read_weight_review
from backend.sleep_entries import list_recent_sleep_entries
from backend.goals import read_goal
from backend.training_preferences import read_training_preferences
from backend.movement_limitations import read_movement_limitations
from backend.food_preferences import read_food_preferences
from backend.energy_preferences import read_energy_inputs
from backend.calorie_previews import read_calorie_preview_inputs
from backend.calorie_proposals import ProposalCursorNotFound, list_calorie_proposals, read_calorie_proposal
from backend.calorie_targets import list_calorie_target_versions, read_target_for_proposal
from backend.services.energy_estimation import EnergyEstimateUnavailable, estimate_adult_energy
from backend.services.food_preferences import MAX_ALLERGIES, MAX_ALLERGY_LENGTH, MAX_MEALS, MAX_PREP_MINUTES
from backend.services.training_preferences import MIN_SESSION_MINUTES, MAX_SESSION_MINUTES
from backend.services.accounts import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from starlette.concurrency import run_in_threadpool
from backend.config import DatabaseConfigurationError
from backend.catalogs import load_exercises
from backend.exercise_readiness import read_exercise_readiness_inputs
from backend.services.catalog_use import exercise_selection_blockers
from backend.services.catalogs import InvalidCatalog
from backend.services.workout_schedule import strength_day_pairs
from backend.routes import templates

router = APIRouter()


@router.get("/sleep-log", response_class=HTMLResponse)
async def sleep_log_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        entries = await run_in_threadpool(list_recent_sleep_entries, identity.user_id)
        today = datetime.now(timezone.utc).astimezone(ZoneInfo(profile.timezone)).date()
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="sleep-log.html", context={
        "entries": entries, "today": today, "timezone": profile.timezone,
        "saved": request.query_params.get("saved") == "1",
    })


@router.get("/weight-review", response_class=HTMLResponse)
async def weight_review_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        review = await run_in_threadpool(read_weight_review, identity.user_id)
        if review is None:
            return RedirectResponse("/profile", status_code=303)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="weight-review.html", context={
        "weeks": review,
    })


@router.get("/weight-log", response_class=HTMLResponse)
async def weight_log_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        entries = await run_in_threadpool(list_recent_weight_entries, identity.user_id)
        today = datetime.now(timezone.utc).astimezone(ZoneInfo(profile.timezone)).date()
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="weight-log.html", context={
        "entries": entries, "today": today, "timezone": profile.timezone,
        "saved": request.query_params.get("saved") == "1",
    })


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


@router.get("/movement-limitations", response_class=HTMLResponse)
async def movement_limitations_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        limitations = await run_in_threadpool(read_movement_limitations, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="movement-limitations.html", context={
        "limitations": limitations,
        "saved": limitations is not None and request.query_params.get("saved") == "1",
    })


@router.get("/workout-readiness", response_class=HTMLResponse)
async def workout_readiness_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        inputs = await run_in_threadpool(read_exercise_readiness_inputs, identity.user_id)
        if inputs is None:
            return RedirectResponse("/profile", status_code=303)
        preferences, limitations = inputs
        exercises = await run_in_threadpool(load_exercises)
        rows = tuple({
            "name": exercise.name,
            "required_equipment": exercise.required_equipment,
            "equipment_ready": "equipment_unavailable" not in exercise_selection_blockers(
                exercises, exercise.id, preferences, limitations,
            ),
        } for exercise in exercises)
        day_pairs = strength_day_pairs(preferences) if preferences is not None else None
    except (DatabaseConfigurationError, SQLAlchemyError, InvalidCatalog):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="workout-readiness.html", context={
        "preferences": preferences, "limitations": limitations, "rows": rows,
        "day_pairs": day_pairs,
        "weekday_names": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    })


@router.get("/food-preferences", response_class=HTMLResponse)
async def food_preferences_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        preferences = await run_in_threadpool(read_food_preferences, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="food-preferences.html", context={
        "preferences": preferences, "timezone": profile.timezone,
        "saved": preferences is not None and request.query_params.get("saved") == "1",
        "max_allergies": MAX_ALLERGIES, "max_allergy_length": MAX_ALLERGY_LENGTH,
        "max_meals": MAX_MEALS, "max_prep_minutes": MAX_PREP_MINUTES,
    })


@router.get("/energy-preferences", response_class=HTMLResponse)
async def energy_preferences_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        inputs = await run_in_threadpool(read_energy_inputs, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    preferences, estimate, unavailable = None, None, None
    if inputs is not None:
        profile, preferences = inputs
        try:
            estimate = estimate_adult_energy(profile, preferences)
        except EnergyEstimateUnavailable as error:
            unavailable = str(error)
    return templates.TemplateResponse(request=request, name="energy-preferences.html", context={
        "profile": profile, "preferences": preferences, "estimate": estimate, "unavailable": unavailable,
        "saved": preferences is not None and request.query_params.get("saved") == "1",
    })


@router.get("/calorie-preview", response_class=HTMLResponse)
async def calorie_preview_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        profile = await run_in_threadpool(read_profile, identity.user_id)
        if profile is None:
            return RedirectResponse("/profile", status_code=303)
        inputs = await run_in_threadpool(read_calorie_preview_inputs, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="calorie-preview.html", context={
        "profile": profile, "goal": inputs[2] if inputs is not None else None,
    })


@router.get("/calorie-proposals/{proposal_id}", response_class=HTMLResponse)
async def calorie_proposal_page(request: Request, proposal_id: UUID):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        proposal = await run_in_threadpool(read_calorie_proposal, identity.user_id, proposal_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    if proposal is None:
        return templates.TemplateResponse(request=request, name="calorie-proposal.html",
                                          status_code=404, context={"proposal": None})
    target = await run_in_threadpool(read_target_for_proposal, identity.user_id, proposal_id)
    return templates.TemplateResponse(request=request, name="calorie-proposal.html",
                                      context={"proposal": proposal, "target": target})


@router.get("/calorie-targets", response_class=HTMLResponse)
async def calorie_targets_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        targets = await run_in_threadpool(list_calorie_target_versions, identity.user_id)
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="calorie-targets.html",
                                      context={"targets": targets})


@router.get("/calorie-proposals", response_class=HTMLResponse)
async def calorie_proposals_page(request: Request):
    try:
        identity = await optional_account(request)
        if identity is None:
            return RedirectResponse("/login", status_code=303)
        query = request.query_params
        if query and (set(query) != {"before"} or len(query.getlist("before")) != 1):
            return templates.TemplateResponse(request=request, name="calorie-proposals.html",
                                              status_code=404, context={"page": None})
        try:
            before = UUID(query["before"]) if query else None
        except ValueError:
            return templates.TemplateResponse(request=request, name="calorie-proposals.html",
                                              status_code=404, context={"page": None})
        try:
            page = await run_in_threadpool(list_calorie_proposals, identity.user_id, before)
        except ProposalCursorNotFound:
            return templates.TemplateResponse(request=request, name="calorie-proposals.html",
                                              status_code=404, context={"page": None})
    except (DatabaseConfigurationError, SQLAlchemyError):
        return templates.TemplateResponse(request=request, name="account.html", status_code=503,
                                          context={"identity": None})
    return templates.TemplateResponse(request=request, name="calorie-proposals.html", context={"page": page})
