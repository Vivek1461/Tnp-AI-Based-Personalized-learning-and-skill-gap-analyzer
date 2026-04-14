from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.data_store import store

_DATA_PATH = Path(__file__).parent / "roadmap_data.json"
_PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}

STAGES = ["beginner", "intermediate", "advanced", "industry_ready"]


def _load() -> Dict[str, Any]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_ROADMAP_DATA: Dict[str, Any] = _load()


def _get_skill_plan(skill: str) -> Optional[Dict[str, Any]]:
    if skill in _ROADMAP_DATA:
        return _ROADMAP_DATA[skill]
    lower = skill.lower()
    for key, val in _ROADMAP_DATA.items():
        if key.lower() == lower:
            return val
    return None


def _make_generic_plan(skill: str) -> Dict[str, Any]:
    return {
        "beginner": {
            "title": f"{skill}: Foundations",
            "time_weeks": 2,
            "concepts": [f"Core {skill} concepts", "Getting started", "Basic tools"],
            "tasks": [f"Complete a {skill} beginner tutorial", f"Build a simple {skill} exercise"],
            "mini_project": f"Beginner project demonstrating basic {skill} skills",
            "milestone": f"Can use {skill} for simple tasks independently",
            "resources": [
                {"name": f"Search '{skill} tutorial' on YouTube", "url": f"https://www.youtube.com/results?search_query={skill}+tutorial", "type": "video"},
                {"name": f"'{skill}' on Coursera (free audit)", "url": f"https://www.coursera.org/search?query={skill}", "type": "course"},
            ],
        },
        "intermediate": {
            "title": f"{skill}: Practical Application",
            "time_weeks": 2,
            "concepts": [f"Intermediate {skill} patterns", "Real-world use cases", "Best practices"],
            "tasks": [f"Complete a hands-on {skill} project", "Solve practice problems"],
            "mini_project": f"Project applying {skill} to a real data or engineering problem",
            "milestone": f"Can apply {skill} to solve medium-complexity real-world problems",
            "resources": [
                {"name": f"{skill} on Kaggle Learn", "url": "https://www.kaggle.com/learn", "type": "interactive"},
            ],
        },
        "advanced": {
            "title": f"{skill}: Advanced Techniques",
            "time_weeks": 3,
            "concepts": [f"Advanced {skill} algorithms/patterns", "Performance optimization", "Edge cases"],
            "tasks": ["Deep-dive into a complex use case", "Contribute to an open source project"],
            "mini_project": f"Advanced {skill} project showcasing depth and complexity",
            "milestone": f"Proficient in {skill} — can handle complex, real-world scenarios",
            "resources": [
                {"name": f"{skill} official documentation", "url": f"https://google.com/search?q={skill}+official+docs", "type": "docs"},
            ],
        },
        "industry_ready": {
            "title": f"{skill}: Production & Interview Ready",
            "time_weeks": 2,
            "concepts": ["Industry patterns", "Integration with other systems", "Interview preparation"],
            "tasks": ["Mock interview for this skill", "Build a portfolio project"],
            "mini_project": f"Portfolio-quality {skill} project suitable for TNP/job applications",
            "milestone": f"Interview-ready for {skill} — can discuss design decisions and trade-offs",
            "resources": [
                {"name": f"Practice {skill} problems on LeetCode/HackerRank", "url": "https://leetcode.com/", "type": "interactive"},
            ],
        },
    }


def generate_roadmap(gaps: List[Dict[str, Any]], user_id: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Given a list of gap dicts (from SkillGapService), returns an ordered
    roadmap prioritized by gap priority (High → Medium → Low).

    Each roadmap item:
    {
        "skill": str,
        "priority": "High|Medium|Low",
        "start_from_stage": str,
        "stages": [
            {
                "stage": str,
                "title": str,
                "time_weeks": int,
                "concepts": [...],
                "tasks": [...],
                "mini_project": str,
                "milestone": str,
                "resources": [{name, url, type}]
            }
        ],
        "total_weeks": int,
        "completion_pct": 0,     # filled by progress tracker at query time
    }
    """
    if user_id and user_id in store.admin_student_roadmap_assignments:
        assigned = store.admin_student_roadmap_assignments[user_id]
        return [
            {
                "skill": item.get("skill", "Custom Plan"),
                "priority": item.get("priority", "High"),
                "start_from_stage": item.get("start_from_stage", "beginner"),
                "stages": item.get("stages", []),
                "total_weeks": item.get("total_weeks", assigned.get("timeline_weeks", 8)),
                "completion_pct": 0,
                "custom_resources": assigned.get("custom_resources", []),
            }
            for item in assigned.get("custom_steps", [])
        ]

    sorted_gaps = sorted(gaps, key=lambda g: _PRIORITY_RANK.get(g.get("priority", "Low"), 2))

    role_override = store.admin_role_roadmap_overrides.get(role or "")

    roadmap: List[Dict[str, Any]] = []
    for gap in sorted_gaps:
        skill = gap.get("skill", "")
        current_score = gap.get("current_score", 0)
        priority = gap.get("priority", "Low")

        plan = _get_skill_plan(skill) or _make_generic_plan(skill)

        # Decide starting stage from current score
        if current_score >= 75:
            start_stage = "industry_ready"
        elif current_score >= 60:
            start_stage = "advanced"
        elif current_score >= 35:
            start_stage = "intermediate"
        else:
            start_stage = "beginner"

        stages_output: List[Dict[str, Any]] = []
        total_weeks = 0
        started = False

        for stage in STAGES:
            if not started and stage != start_stage:
                continue
            started = True
            stage_data = plan.get(stage, {})
            if not stage_data:
                continue
            stages_output.append({
                "stage": stage,
                "title": stage_data.get("title", f"{skill} – {stage}"),
                "time_weeks": stage_data.get("time_weeks", 2),
                "concepts": stage_data.get("concepts", []),
                "tasks": stage_data.get("tasks", []),
                "mini_project": stage_data.get("mini_project", ""),
                "milestone": stage_data.get("milestone", ""),
                "resources": stage_data.get("resources", []),
            })
            total_weeks += stage_data.get("time_weeks", 2)

        roadmap.append({
            "skill": skill,
            "priority": priority,
            "start_from_stage": start_stage,
            "stages": stages_output,
            "total_weeks": total_weeks,
            "completion_pct": 0,
            "custom_resources": role_override.get("custom_resources", []) if role_override else [],
        })

    return roadmap
