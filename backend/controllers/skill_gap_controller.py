from __future__ import annotations

from backend.models.schemas import SkillGapResponse
from backend.services.skill_gap_service import SkillGapService


def analyze_skill_gap(user: dict) -> SkillGapResponse:
    data = SkillGapService.analyze(user)
    return SkillGapResponse(**data)
