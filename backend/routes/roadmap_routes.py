from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.middleware.auth import get_current_user
from backend.modules.roadmap_generator.generator import generate_roadmap
from backend.services.data_store import store
from backend.services.skill_gap_service import SkillGapService

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


@router.get("")
def get_roadmap(
    company: Optional[str] = Query(None, description="Company name for role-specific requirements"),
    role: Optional[str] = Query(None, description="Override target role"),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Generate a prioritized learning roadmap based on the user's skill gaps.
    Requires assessment to have been completed first.
    """
    resolved_role = role or store.user_target_roles.get(user["id"]) or user.get("target_role")
    gap_analysis = SkillGapService.analyze({**user, "target_role": resolved_role}, company=company, role=resolved_role)
    gaps = gap_analysis.get("gaps", [])

    roadmap = generate_roadmap(gaps, user_id=user["id"], role=resolved_role)

    total_weeks = sum(item.get("total_weeks", 0) for item in roadmap)

    role_override = store.admin_role_roadmap_overrides.get(resolved_role, {})
    company_role_requirements = {}
    if company and company in store.company_role_requirements:
        company_role_requirements = store.company_role_requirements[company].get(resolved_role, {})

    admin_preferred_suggestions = {
        "role": resolved_role,
        "company": company,
        "preferred_custom_steps": role_override.get("custom_steps", []),
        "preferred_custom_resources": role_override.get("custom_resources", []),
        "preferred_focus_skills": [
            {
                "skill": s,
                "weight": info.get("weight_label", "Medium"),
                "required_score": info.get("required_score", 0),
            }
            for s, info in company_role_requirements.items()
        ],
        "personalized_resources_for_student": store.admin_student_resource_recommendations.get(user["id"], []),
    }

    return {
        "target_role": gap_analysis["target_role"],
        "company": company,
        "readiness_percent": gap_analysis["readiness_percent"],
        "total_gap_count": len(gaps),
        "estimated_total_weeks": total_weeks,
        "admin_preferred_suggestions": admin_preferred_suggestions,
        "roadmap": roadmap,
    }
