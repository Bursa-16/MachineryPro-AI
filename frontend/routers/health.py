"""Health-check endpoint (UI-0A).

Returns a JSON object confirming the application is running and the
deterministic engineering core is importable.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return application health status."""
    # Verify that the engineering backend is importable.
    try:
        from backend.domain.result import EngineeringResult  # noqa: F401

        core_status = "online"
    except Exception:
        core_status = "unavailable"

    return {
        "status": "ok",
        "application": "MachineryPro AI",
        "version": "0.1.0",
        "engineering_core": core_status,
    }
