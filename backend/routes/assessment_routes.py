from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends

from backend.controllers.assessment_controller import get_assessment_result, start_assessment, submit_assessment
from backend.middleware.auth import get_current_user
from backend.models.schemas import AssessmentSubmitRequest
from backend.services.assessment_service import AssessmentService
from backend.services.adaptive_engine import (
    start_adaptive_session,
    submit_adaptive_answer,
    get_next_question,
)

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


# ── Legacy / batch endpoints (backward-compatible) ────────────────────────────

@router.get("/start")
def start(user: dict = Depends(get_current_user)):
    """Batch mode: returns all MCQ questions for target role skills at once."""
    return start_assessment(user)


@router.post("/submit")
def submit(payload: AssessmentSubmitRequest, user: dict = Depends(get_current_user)):
    """Legacy: submit manual scores per skill (backward-compatible)."""
    return submit_assessment(user, payload)


@router.post("/evaluate")
def evaluate_answers(
    answers: Dict[str, List[int]],
    user: dict = Depends(get_current_user),
):
    """
    Batch: Submit all MCQ answers at once and get weighted skill scores.
    Body: { "question_id": [selected_option_indices], ... }
    """
    return AssessmentService.evaluate_answers(user, answers)


@router.get("/result")
def result(user: dict = Depends(get_current_user)):
    """Get the stored assessment result with skill levels."""
    return get_assessment_result(user)


# ── Adaptive endpoints (new) ──────────────────────────────────────────────────

@router.post("/adaptive/start")
def adaptive_start(user: dict = Depends(get_current_user)):
    """
    Start an adaptive assessment session.
    Returns the first question and session progress.
    Difficulty adapts automatically: correct → harder, wrong → easier.
    """
    return start_adaptive_session(user)


@router.get("/adaptive/next")
def adaptive_next(user: dict = Depends(get_current_user)):
    """
    Get the next question in the current adaptive session
    without submitting an answer (e.g., after page refresh).
    """
    return get_next_question(user)


@router.post("/adaptive/answer")
def adaptive_answer(
    payload: dict,
    user: dict = Depends(get_current_user),
):
    """
    Submit a single answer for the adaptive session.
    Body: { "question_id": "py-3", "selected": [0, 2] }
    Returns: { correct, correct_answers, next_question | results_if_done }
    """
    q_id: str = payload.get("question_id", "")
    selected: List[int] = payload.get("selected", [])
    return submit_adaptive_answer(user, q_id, selected)
