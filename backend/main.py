"""Compose the web shell without starting database or model operations."""

from contextlib import asynccontextmanager
from pathlib import Path
from threading import BoundedSemaphore

from fastapi import FastAPI
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.exc import SQLAlchemyError

from backend.account_pages import router as account_pages_router
from backend.accounts import InvalidCredentials, UsernameUnavailable
from backend.auth_routes import router as auth_router
from backend.config import DatabaseConfigurationError
from backend.database import close_database
from backend.services.accounts import InvalidAccountInput
from backend.routes import router
from backend.profile_routes import router as profile_router
from backend.services.profiles import InvalidProfile
from backend.services.goals import InvalidGoal
from backend.services.training_preferences import InvalidTrainingPreferences
from backend.training_preference_routes import router as training_preference_router
from backend.goals import GoalProfileRequired
from backend.goal_routes import router as goal_router
from backend.rate_limits import AttemptLimiter
from backend.http_limits import HttpLimitsMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app):
    try:
        yield
    finally:
        close_database()


def create_app() -> FastAPI:
    app = FastAPI(
        title="TrainAI", version="0.1.0", debug=False, lifespan=lifespan,
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.state.auth_slots = BoundedSemaphore(2)
    app.state.auth_attempts = AttemptLimiter()

    async def account_error(request, error):
        status = 422
        if isinstance(error, InvalidCredentials):
            status = 401
        elif isinstance(error, (UsernameUnavailable, GoalProfileRequired)):
            status = 409
        return JSONResponse({"detail": str(error)}, status_code=status)

    for error_type in [InvalidAccountInput, InvalidCredentials, UsernameUnavailable, InvalidProfile, InvalidGoal, GoalProfileRequired, InvalidTrainingPreferences]:
        app.add_exception_handler(error_type, account_error)

    async def persistence_error(request, error):
        return JSONResponse(
            {"detail": "Account storage is unavailable. Try again after configuration is checked."},
            status_code=503,
        )

    for error_type in [DatabaseConfigurationError, SQLAlchemyError]:
        app.add_exception_handler(error_type, persistence_error)

    @app.exception_handler(ResponseValidationError)
    async def invalid_response(request, error):
        return JSONResponse({"detail": "The response could not be completed."}, status_code=500)

    app.add_middleware(HttpLimitsMiddleware)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"]
    )

    @app.middleware("http")
    async def set_browser_policies(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; font-src 'self'; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    app.mount(
        "/static", StaticFiles(directory=PROJECT_ROOT / "frontend" / "static"),
        name="static",
    )
    app.include_router(router)
    app.include_router(auth_router)
    app.include_router(account_pages_router)
    app.include_router(profile_router)
    app.include_router(goal_router)
    app.include_router(training_preference_router)
    return app


app = create_app()
