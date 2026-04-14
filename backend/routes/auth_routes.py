from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.controllers.auth_controller import (
    get_profile,
    login_user,
    register_user,
    update_profile,
)
from backend.middleware.auth import get_current_user
from backend.models.schemas import AuthResponse, LoginRequest, ProfileResponse, ProfileUpdateRequest, RegisterRequest

router = APIRouter(prefix="/api", tags=["auth-profile"])


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    return register_user(payload)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    return login_user(payload)


@router.get("/profile", response_model=ProfileResponse)
def profile(user: dict = Depends(get_current_user)) -> ProfileResponse:
    return get_profile(user)


@router.put("/update-profile", response_model=ProfileResponse)
def update(payload: ProfileUpdateRequest, user: dict = Depends(get_current_user)) -> ProfileResponse:
    return update_profile(user, payload)
