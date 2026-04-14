from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.admin.admin_controller import (
    admin_login,
    assign_roadmap,
    create_custom_test,
    create_question,
    create_role,
    delete_question,
    delete_role,
    get_admin_snapshot,
    get_students_analytics,
    list_questions,
    update_question,
    update_role,
    upsert_role_roadmap_override,
)
from backend.admin.admin_service import AdminService


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)


class SkillRequirementIn(BaseModel):
    skill: str
    weight: str = "Medium"
    minimum_score_required: int = Field(default=70, ge=0, le=100)


class RoleUpsertRequest(BaseModel):
    company: str
    role: str
    skills: List[SkillRequirementIn]


class RoleUpdateRequest(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[List[SkillRequirementIn]] = None


class QuestionUpsertRequest(BaseModel):
    question: str
    type: str = "MCQ"
    skill: str
    difficulty: str = "Medium"
    weight: int = Field(default=1, ge=1, le=10)
    options: List[str] = Field(default_factory=list)
    correct_answers: List[int] = Field(default_factory=list)


class QuestionUpdateRequest(BaseModel):
    question: Optional[str] = None
    type: Optional[str] = None
    skill: Optional[str] = None
    difficulty: Optional[str] = None
    weight: Optional[int] = Field(default=None, ge=1, le=10)
    options: Optional[List[str]] = None
    correct_answers: Optional[List[int]] = None


class CustomTestRequest(BaseModel):
    name: str
    question_ids: List[str]
    role_id: Optional[str] = None
    student_id: Optional[str] = None


class AssignRoadmapRequest(BaseModel):
    student_id: str
    role: Optional[str] = None
    timeline_weeks: int = Field(default=8, ge=1, le=52)
    difficulty_progression: List[str] = Field(default_factory=lambda: ["beginner", "intermediate", "advanced"])
    custom_steps: List[dict] = Field(default_factory=list)
    custom_resources: List[dict] = Field(default_factory=list)
    recommended_resources: List[dict] = Field(default_factory=list)


class RoleRoadmapOverrideRequest(BaseModel):
    role: str
    timeline_weeks: int = Field(default=8, ge=1, le=52)
    difficulty_progression: List[str] = Field(default_factory=lambda: ["beginner", "intermediate", "advanced"])
    custom_steps: List[dict] = Field(default_factory=list)
    custom_resources: List[dict] = Field(default_factory=list)


def get_current_admin(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing admin bearer token")
    token = authorization.replace("Bearer ", "", 1).strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing admin bearer token")
    return AdminService.get_admin_by_token(token)


router = APIRouter(prefix="/api/admin", tags=["admin-control"])


@router.post("/login")
def login(payload: AdminLoginRequest) -> dict:
    return admin_login(payload)


@router.get("/snapshot")
def snapshot(_: dict = Depends(get_current_admin)) -> dict:
    return get_admin_snapshot()


@router.post("/role")
def create_role_api(payload: RoleUpsertRequest, _: dict = Depends(get_current_admin)) -> dict:
    return create_role(payload)


@router.put("/role/{role_id}")
def update_role_api(role_id: str, payload: RoleUpdateRequest, _: dict = Depends(get_current_admin)) -> dict:
    return update_role(role_id, payload)


@router.delete("/role/{role_id}")
def delete_role_api(role_id: str, _: dict = Depends(get_current_admin)) -> dict:
    return delete_role(role_id)


@router.post("/question")
def create_question_api(payload: QuestionUpsertRequest, _: dict = Depends(get_current_admin)) -> dict:
    return create_question(payload)


@router.put("/question/{question_id}")
def update_question_api(question_id: str, payload: QuestionUpdateRequest, _: dict = Depends(get_current_admin)) -> dict:
    return update_question(question_id, payload)


@router.delete("/question/{question_id}")
def delete_question_api(question_id: str, _: dict = Depends(get_current_admin)) -> dict:
    return delete_question(question_id)


@router.get("/questions")
def list_questions_api(_: dict = Depends(get_current_admin)) -> dict:
    return list_questions()


@router.post("/tests")
def create_custom_test_api(payload: CustomTestRequest, _: dict = Depends(get_current_admin)) -> dict:
    return create_custom_test(payload)


@router.post("/roadmap-override")
def role_roadmap_override_api(payload: RoleRoadmapOverrideRequest, _: dict = Depends(get_current_admin)) -> dict:
    return upsert_role_roadmap_override(payload)


@router.get("/students")
def students_api(_: dict = Depends(get_current_admin)) -> dict:
    return get_students_analytics()


@router.post("/assign-roadmap")
def assign_roadmap_api(payload: AssignRoadmapRequest, _: dict = Depends(get_current_admin)) -> dict:
    return assign_roadmap(payload)
