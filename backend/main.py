"""Compose the web shell without starting database or model operations."""

from contextlib import asynccontextmanager
from pathlib import Path
from threading import BoundedSemaphore

from fastapi import FastAPI
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

    async def account_error(request, error):
        status = 422
        if isinstance(error, InvalidCredentials):
            status = 401
        elif isinstance(error, UsernameUnavailable):
            status = 409
        return JSONResponse({"detail": str(error)}, status_code=status)

    for error_type in [InvalidAccountInput, InvalidCredentials, UsernameUnavailable]:
        app.add_exception_handler(error_type, account_error)

    async def persistence_error(request, error):
        return JSONResponse(
            {"detail": "Account storage is unavailable. Try again after configuration is checked."},
            status_code=503,
        )

    for error_type in [DatabaseConfigurationError, SQLAlchemyError]:
        app.add_exception_handler(error_type, persistence_error)

    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"]
    )

    @app.middleware("http")
    async def set_browser_policies(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
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
    return app


app = create_app()
