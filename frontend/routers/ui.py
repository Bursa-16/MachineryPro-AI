"""UI page router (UI-0A).

Serves the Jinja2-rendered HTML pages for the engineering interface.
All pages extend ``base.html`` which provides the sidebar navigation
and Tailwind/HTMX integration.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

# -- Navigation definition (single source of truth) -----------------------

NAV_ITEMS: list[dict[str, str]] = [
    {"label": "Dashboard", "href": "/ui/", "icon": "home", "badge": ""},
    {"label": "CAD Import", "href": "/ui/cad-import", "icon": "upload", "badge": ""},
    {"label": "Geometry / Topology", "href": "/ui/geometry", "icon": "box", "badge": ""},
    {"label": "Machining", "href": "/ui/machining", "icon": "settings", "badge": ""},
    {"label": "Tools & Parameters", "href": "/ui/tools", "icon": "wrench", "badge": ""},
    {"label": "Materials", "href": "/ui/materials", "icon": "layers", "badge": "PLANNED"},
    {"label": "Validation", "href": "/ui/validation", "icon": "shield-check", "badge": ""},
    {"label": "AI Assistant", "href": "/ui/ai-assistant", "icon": "sparkles", "badge": "PLANNED"},
]

# -- Dashboard capability cards --------------------------------------------

DASHBOARD_CARDS: list[dict[str, str]] = [
    {
        "title": "CAD Interoperability",
        "description": "STEP · DXF · IGES import with canonical geometry and topology extraction.",
        "status": "READY",
        "stage": "Stage 4A–4F",
    },
    {
        "title": "Machining Engineering",
        "description": (
            "Turning · Drilling · Milling · Threading · Hole Finishing "
            "with deterministic formulas and engineering rules."
        ),
        "status": "READY",
        "stage": "Stage 3",
    },
    {
        "title": "DFM Validation",
        "description": (
            "Design-for-manufacturability checks: hole-tool diameter, corner radius, "
            "slot width, pocket access, depth/diameter ratio."
        ),
        "status": "READY",
        "stage": "Stage 3",
    },
    {
        "title": "Process Planning",
        "description": (
            "Deterministic plan builder with acyclicity validation, "
            "predecessor checks, and aggregate status."
        ),
        "status": "READY",
        "stage": "Stage 3J",
    },
]


def _context(*, active_href: str, **extra: object) -> dict[str, object]:
    """Build the standard template context (without request)."""
    return {
        "nav_items": NAV_ITEMS,
        "active_href": active_href,
        **extra,
    }


def _render(
    request: Request,
    template_name: str,
    ctx: dict[str, object],
) -> HTMLResponse:
    """Render a Jinja2 template using the Starlette-compatible API."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        template_name,
        ctx,
    )


# -- Routes ----------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Redirect root to dashboard."""
    return _render(
        request,
        "index.html",
        _context(active_href="/ui/", cards=DASHBOARD_CARDS),
    )


@router.get("/ui/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Dashboard / project home."""
    return _render(
        request,
        "index.html",
        _context(active_href="/ui/", cards=DASHBOARD_CARDS),
    )
