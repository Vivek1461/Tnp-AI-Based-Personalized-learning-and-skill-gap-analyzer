from __future__ import annotations

from backend.models.schemas import (
    AuthResponse,
    CareerPathsResponse,
    LoginRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    RegisterRequest,
)
from backend.services.auth_service import AuthService
from backend.services.data_store import store


def register_user(payload: RegisterRequest) -> AuthResponse:
    user = AuthService.register(payload)
    token, user = AuthService.login(LoginRequest(username=user["username"], password=payload.password))
    return AuthResponse(access_token=token, user=ProfileResponse(**_public_user(user)))


def login_user(payload: LoginRequest) -> AuthResponse:
    token, user = AuthService.login(payload)
    return AuthResponse(access_token=token, user=ProfileResponse(**_public_user(user)))


def get_profile(user: dict) -> ProfileResponse:
    return ProfileResponse(**_public_user(user))


def update_profile(user: dict, payload: ProfileUpdateRequest) -> ProfileResponse:
    updated = AuthService.update_profile(user, payload)
    return ProfileResponse(**_public_user(updated))


def list_career_paths() -> CareerPathsResponse:
    return CareerPathsResponse(roles=store.career_paths)


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "student_id": user.get("student_id"),
        "username": user.get("username"),
        "name": user["name"],
        "email": user["email"],
        "education_level": user.get("education_level"),
        "current_skills": user.get("current_skills", []),
        "target_role": user.get("target_role"),
        "learning_goals": user.get("learning_goals", []),
    }
