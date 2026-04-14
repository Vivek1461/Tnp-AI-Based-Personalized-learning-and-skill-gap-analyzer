from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    student_id: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    education_level: Optional[str] = None
    current_skills: List[str] = Field(default_factory=list)
    target_role: Optional[str] = None
    learning_goals: List[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

    @model_validator(mode="after")
    def validate_identifier(self) -> "LoginRequest":
        if not self.username and not self.email:
            raise ValueError("username or email is required")
        return self


class ProfileResponse(BaseModel):
    id: str
    student_id: Optional[str] = None
    username: Optional[str] = None
    name: str
    email: EmailStr
    education_level: Optional[str] = None
    current_skills: List[str] = Field(default_factory=list)
    target_role: Optional[str] = None
    learning_goals: List[str] = Field(default_factory=list)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: ProfileResponse


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    education_level: Optional[str] = None
    current_skills: Optional[List[str]] = None
    target_role: Optional[str] = None
    learning_goals: Optional[List[str]] = None


class CareerPathsResponse(BaseModel):
    roles: Dict[str, Dict[str, int]]


class AssessmentQuestion(BaseModel):
    id: str
    skill: str
    type: str
    prompt: str


class AssessmentStartResponse(BaseModel):
    target_role: str
    questions: List[AssessmentQuestion]


class AssessmentSubmitRequest(BaseModel):
    scores: Dict[str, int]


class AssessmentResultResponse(BaseModel):
    user_id: str
    target_role: Optional[str]
    scores: Dict[str, int]


class SkillGapItem(BaseModel):
    skill: str
    required_level: int
    current_level: int
    gap: int
    status: str


class SkillGapResponse(BaseModel):
    target_role: str
    readiness_percent: int
    summary: str
    skills: List[SkillGapItem]
