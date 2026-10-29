"""Public pages and web-process health; no private records are accepted yet."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "frontend" / "templates"
)
router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/health")
def health() -> dict[str, str]:
    """Report only web-process health, not database or AI readiness."""
    return {"status": "ok", "scope": "web", "ai": "not_configured"}
