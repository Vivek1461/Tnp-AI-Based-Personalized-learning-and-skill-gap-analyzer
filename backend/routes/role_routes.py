from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.modules.role_mapper.role_mapper import (
    get_all_roles_flat,
    get_companies,
    get_roles,
    get_skill_requirements,
)

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("")
def list_companies() -> dict:
    """Return all available companies."""
    return {"companies": get_companies()}


@router.get("/all")
def list_all_roles() -> dict:
    """Return a flat list of all company-role combinations."""
    return {"roles": get_all_roles_flat()}


@router.get("/{company}")
def list_roles_for_company(company: str) -> dict:
    """Return available roles for a given company."""
    roles = get_roles(company)
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company}' not found. Use GET /api/roles to see available companies.",
        )
    return {"company": company, "roles": roles}


@router.get("/{company}/{role}")
def get_role_requirements(company: str, role: str) -> dict:
    """Return skill requirements for a specific company + role."""
    reqs = get_skill_requirements(company, role)
    if reqs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role}' not found for company '{company}'",
        )
    return {
        "company": company,
        "role": role,
        "skills": reqs,
    }
