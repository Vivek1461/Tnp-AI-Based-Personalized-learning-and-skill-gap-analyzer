from __future__ import annotations

from fastapi import APIRouter

from backend.controllers.auth_controller import list_career_paths
from backend.models.schemas import CareerPathsResponse

router = APIRouter(prefix="/api", tags=["career"])


@router.get("/career-paths", response_model=CareerPathsResponse)
def get_career_paths() -> CareerPathsResponse:
    return list_career_paths()
