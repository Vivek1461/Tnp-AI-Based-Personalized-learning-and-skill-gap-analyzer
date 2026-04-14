from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from backend.services.data_store import store

STAGES = ["beginner", "intermediate", "advanced"]


def _get_progress(user_id: str) -> Dict[str, Dict[str, bool]]:
    """Return progress dict for a user, creating it if absent."""
    if user_id not in store.roadmap_progress:
        store.roadmap_progress[user_id] = {}
    return store.roadmap_progress[user_id]


def mark_complete(user_id: str, skill: str, stage: str) -> dict:
    """Mark a skill+stage as completed for a user."""
    progress = _get_progress(user_id)
    if skill not in progress:
        progress[skill] = {s: False for s in STAGES}
    stage = stage.lower()
    if stage not in STAGES:
        raise ValueError(f"Invalid stage '{stage}'. Must be one of {STAGES}")
    progress[skill][stage] = True
    return {"skill": skill, "stage": stage, "completed": True}


def get_user_progress(user_id: str) -> Dict[str, Dict[str, bool]]:
    return _get_progress(user_id)


def compute_metrics(user_id: str) -> dict:
    """
    Calculate:
    - overall_completion_pct: ratio of completed stages
    - skill_completion: per-skill completion percentage
    - gap_reduction_pct: estimated gap reduction based on completed stages
    """
    progress = _get_progress(user_id)
    if not progress:
        return {
            "overall_completion_pct": 0,
            "skill_completion": {},
            "gap_reduction_pct": 0,
            "completed_items": 0,
            "total_items": 0,
        }

    total_items = 0
    completed_items = 0
    skill_completion: Dict[str, int] = {}

    for skill, stages in progress.items():
        skill_total = len(stages)
        skill_done = sum(1 for done in stages.values() if done)
        total_items += skill_total
        completed_items += skill_done
        pct = round((skill_done / skill_total) * 100) if skill_total else 0
        skill_completion[skill] = pct

    overall_pct = round((completed_items / total_items) * 100) if total_items else 0

    # Gap reduction: each completed stage reduces the gap by ~33% for that skill
    # Estimated overall: weighted by completion
    gap_reduction = round(overall_pct * 0.85)  # learning doesn't instantly close gap

    return {
        "overall_completion_pct": overall_pct,
        "skill_completion": skill_completion,
        "gap_reduction_pct": gap_reduction,
        "completed_items": completed_items,
        "total_items": total_items,
    }
