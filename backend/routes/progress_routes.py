from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status

from backend.middleware.auth import get_current_user
from backend.modules.progress_tracker.tracker import (
    compute_metrics,
    get_user_progress,
    mark_complete,
)

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
def get_progress(user: dict = Depends(get_current_user)) -> dict:
    """Return current progress and computed metrics for the logged-in user."""
    progress = get_user_progress(user["id"])
    metrics = compute_metrics(user["id"])
    return {
        "user_id": user["id"],
        "progress": progress,
        "metrics": metrics,
    }


@router.post("/complete")
def mark_item_complete(
    skill: str = Body(..., embed=True),
    stage: str = Body(..., embed=True),
    user: dict = Depends(get_current_user),
) -> dict:
    """Mark a roadmap stage as completed (skill + stage: beginner|intermediate|advanced)."""
    try:
        result = mark_complete(user["id"], skill, stage)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    metrics = compute_metrics(user["id"])
    return {
        "message": f"Marked {skill} ({stage}) as complete",
        "result": result,
        "metrics": metrics,
    }


@router.delete("/reset")
def reset_progress(user: dict = Depends(get_current_user)) -> dict:
    """Reset all progress for the current user."""
    from backend.services.data_store import store
    store.roadmap_progress[user["id"]] = {}
    return {"message": "Progress reset successfully"}
