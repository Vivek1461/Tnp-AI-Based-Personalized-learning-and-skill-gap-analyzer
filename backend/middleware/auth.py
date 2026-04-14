from __future__ import annotations

from fastapi import Header, HTTPException, status

from backend.services.auth_service import AuthService


def get_current_user(authorization: str = Header(default="")) -> dict:
    """Extract and validate bearer token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1).strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    return AuthService.get_user_by_token(token)
