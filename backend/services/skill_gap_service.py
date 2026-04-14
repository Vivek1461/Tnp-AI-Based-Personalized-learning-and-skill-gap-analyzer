from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from backend.services.data_store import store


class SkillGapService:
    """
    Advanced skill gap analyzer:
    - 3-signal analysis: resume presence + assessment score + role requirement
    - Explainability: each gap includes reason + evidence
    - Weighted priority: skill importance × score deficit
    - Penalty for skills missing from resume (caps theoretical knowledge at 40%)
    """

    # Weight label → numeric multiplier for priority calculation
    _WEIGHT_MULTIPLIER = {"High": 3, "Medium": 2, "Low": 1}

    @staticmethod
    def _status_for_score(score: int) -> str:
        if score >= 80:
            return "Good"
        if score >= 60:
            return "Average"
        if score >= 40:
            return "Weak"
        return "Beginner"

    @staticmethod
    def _compute_priority(required: int, current: int, weight_label: str) -> str:
        gap = max(required - current, 0)
        weight = SkillGapService._WEIGHT_MULTIPLIER.get(weight_label, 1)
        priority_score = gap * weight / 100.0

        if priority_score >= 1.5:
            return "High"
        if priority_score >= 0.5:
            return "Medium"
        return "Low"

    @staticmethod
    def analyze(user: dict, company: Optional[str] = None, role: Optional[str] = None) -> dict:
        """
        Analyze skill gaps.

        Uses:
        - user.target_role (fallback) or explicit role param
        - store.career_paths for required levels
        - store.assessment_results for current performance scores
        - store.resume_data for resume-detected skills

        Returns explainable gap list.
        """
        target_role = role or store.user_target_roles.get(user["id"]) or user.get("target_role")
        if not target_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target role is not set")

        # Get skill requirements
        required_map: Optional[Dict[str, Any]] = None
        weight_map: Dict[str, str] = {}

        if company:
            # Try role_mapper for company-specific requirements
            try:
                from backend.modules.role_mapper.role_mapper import get_skill_requirements
                role_reqs = get_skill_requirements(company, target_role)
                if role_reqs:
                    required_map = {skill: info["required_score"] for skill, info in role_reqs.items()}
                    weight_map = {skill: info["weight_label"] for skill, info in role_reqs.items()}
            except ImportError:
                pass

        if not required_map:
            required_map = store.career_paths.get(target_role)
            if not required_map:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career role not found")
            # Default all weights to Medium if not specified
            weight_map = {skill: "High" if req >= 80 else "Medium" for skill, req in required_map.items()}

        current_scores = store.assessment_results.get(user["id"])
        if not current_scores:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assessment result found. Please complete the assessment first.")

        # Resume skills (may be empty if not uploaded)
        resume_data: dict = store.resume_data.get(user["id"], {})
        resume_skills: List[str] = resume_data.get("normalized_skills", resume_data.get("skills", []))
        # Also include skills declared at registration
        resume_skills = list(set(resume_skills + user.get("current_skills", [])))

        gaps = []
        readiness_ratios = []

        for skill, required_level in required_map.items():
            raw_score = current_scores.get(skill, 0)
            in_resume = any(s.lower() == skill.lower() for s in resume_skills)
            weight_label = weight_map.get(skill, "Medium")

            # Apply resume penalty: if skill not in resume, cap at 40%
            if not in_resume and raw_score > 40:
                current_level = 40
            else:
                current_level = int(raw_score)

            gap = max(required_level - current_level, 0)
            ratio = min(current_level / required_level, 1.0) if required_level else 1.0
            readiness_ratios.append(ratio)

            priority = SkillGapService._compute_priority(required_level, current_level, weight_label)

            # Build reason + evidence
            if not in_resume and raw_score == 0:
                reason = f"Required for {target_role} but completely absent from resume and assessment"
                evidence = "Not found in resume; score: 0"
            elif not in_resume and raw_score > 0:
                reason = f"Theoretical knowledge detected in assessment but not validated by resume/experience"
                evidence = f"Resume: absent (practical score capped at 40); Assessment: {raw_score}"
            elif raw_score < 40:
                reason = f"Skill present in resume but assessment reveals very weak proficiency"
                evidence = f"Assessment score: {raw_score}/100 (below 40 threshold)"
            elif raw_score < required_level:
                reason = f"Skill assessed but does not yet meet the required level for {target_role}"
                evidence = f"Current score: {raw_score}/100; Required: {required_level}/100"
            else:
                reason = "Skill meets role requirement"
                evidence = f"Score: {raw_score}/100 ≥ Required: {required_level}/100"

            gaps.append({
                "skill": skill,
                "required_level": required_level,
                "current_level": current_level,
                "raw_score": raw_score,
                "gap": gap,
                "status": SkillGapService._status_for_score(current_level),
                "priority": priority,
                "weight_label": weight_label,
                "in_resume": in_resume,
                "reason": reason,
                "evidence": evidence,
                "current_score": current_level,
            })

        # Sort: high priority first
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        gaps.sort(key=lambda g: priority_order.get(g["priority"], 2))

        readiness_percent = round((sum(readiness_ratios) / len(readiness_ratios)) * 100) if readiness_ratios else 0
        company_str = f" at {company}" if company else ""
        summary = f"You are {readiness_percent}% ready for the {target_role} role{company_str}"

        return {
            "target_role": target_role,
            "company": company,
            "readiness_percent": readiness_percent,
            "summary": summary,
            "skills": gaps,
            "gaps": [g for g in gaps if g["gap"] > 0],  # only actual gaps for roadmap
        }
