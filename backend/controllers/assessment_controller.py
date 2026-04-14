from __future__ import annotations

from backend.services.assessment_service import AssessmentService


def start_assessment(user: dict) -> dict:
    return AssessmentService.start_assessment(user)


def submit_assessment(user: dict, payload) -> dict:
    """Calls the legacy manual-score submission, returns enriched result dict."""
    return AssessmentService.submit_assessment(user, payload)


def get_assessment_result(user: dict) -> dict:
    return AssessmentService.get_assessment_result(user)
