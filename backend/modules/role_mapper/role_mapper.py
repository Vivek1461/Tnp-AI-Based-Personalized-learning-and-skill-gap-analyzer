from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.data_store import store

_DATA_PATH = Path(__file__).parent / "role_data.json"

# Weight string → numeric score requirement modifier
WEIGHT_SCORE_MAP = {"High": 85, "Medium": 70, "Low": 55}
WEIGHT_PRIORITY_MAP = {"High": 3, "Medium": 2, "Low": 1}


def _load() -> Dict[str, Any]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_DATA: Dict[str, Any] = _load()


def _merged_company_data() -> Dict[str, Any]:
    # Runtime admin-managed requirements are authoritative.
    merged = dict(_DATA)
    for company, role_map in store.company_role_requirements.items():
        merged.setdefault(company, {})
        merged[company].update(role_map)
    return merged


def get_companies() -> List[str]:
    return sorted(_merged_company_data().keys())


def get_roles(company: str) -> List[str]:
    company_data = _merged_company_data().get(company)
    if not company_data:
        return []
    return sorted(company_data.keys())


def get_skill_requirements(company: str, role: str) -> Optional[Dict[str, Any]]:
    """
    Returns a dict of skill -> {weight_label, required_score, priority_value}
    or None if the company/role combo is not found.
    """
    company_data = _merged_company_data().get(company)
    if not company_data:
        return None
    role_data = company_data.get(role)
    if not role_data:
        return None

    # If already in expanded format, return as-is.
    if role_data and isinstance(next(iter(role_data.values())), dict):
        return role_data

    result = {}
    for skill, weight_label in role_data.items():
        result[skill] = {
            "weight_label": weight_label,
            "required_score": WEIGHT_SCORE_MAP.get(weight_label, 70),
            "priority_value": WEIGHT_PRIORITY_MAP.get(weight_label, 1),
        }
    return result


def get_all_roles_flat() -> List[Dict[str, str]]:
    """Return a flat list of {company, role} dicts for UI dropdowns."""
    items = []
    for company, roles in _merged_company_data().items():
        for role in roles:
            items.append({"company": company, "role": role})
    return items
