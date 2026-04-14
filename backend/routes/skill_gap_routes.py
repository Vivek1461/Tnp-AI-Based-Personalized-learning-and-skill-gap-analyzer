from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.middleware.auth import get_current_user
from backend.services.skill_gap_service import SkillGapService

router = APIRouter(prefix="/api/skill-gap", tags=["skill-gap"])


@router.get("/analyze")
def analyze_skill_gap(
    company: Optional[str] = Query(None, description="Company name (e.g. TCS, Google)"),
    role: Optional[str] = Query(None, description="Override target role"),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Analyze skill gaps with explainability.
    Compares resume skills + assessment scores against role requirements.
    Optional ?company=TCS&role=Data+Analyst for company-specific requirements.
    """
    return SkillGapService.analyze(user, company=company, role=role)
