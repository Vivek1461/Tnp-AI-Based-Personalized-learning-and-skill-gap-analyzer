from __future__ import annotations

import json
import hashlib
import hmac
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status

from backend.models.schemas import LoginRequest, ProfileUpdateRequest, RegisterRequest
from backend.services.data_store import store


class AuthService:
    _AUTH_DATA_PATH = Path(__file__).parent / "auth_data.json"
    _auth_loaded = False

    @staticmethod
    def _load_persisted_auth() -> None:
        if AuthService._auth_loaded:
            return
        AuthService._auth_loaded = True

        if not AuthService._AUTH_DATA_PATH.exists():
            return

        try:
            with open(AuthService._AUTH_DATA_PATH, encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            return

        users = payload.get("users", [])
        sessions = payload.get("sessions", {})

        for user in users:
            user_id = user.get("id")
            email = user.get("email")
            student_id = user.get("student_id")
            if not user_id or not email:
                continue
            store.users_by_id[user_id] = user
            store.users_by_email[email] = user
            if student_id:
                store.users_by_student_id[student_id] = user

        # Keep persisted sessions if users still exist
        for token, user_id in sessions.items():
            if user_id in store.users_by_id:
                store.sessions[token] = user_id

    @staticmethod
    def _persist_auth() -> None:
        users = list(store.users_by_id.values())
        payload = {
            "users": users,
            "sessions": store.sessions,
        }
        with open(AuthService._AUTH_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2)

    @staticmethod
    def _normalize_student_id(student_id: str) -> str:
        return student_id.strip().upper().replace(" ", "")

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return digest.hex()

    @staticmethod
    def _create_password_record(password: str) -> str:
        salt = os.urandom(16).hex()
        hashed = AuthService._hash_password(password, salt)
        return f"{salt}${hashed}"

    @staticmethod
    def _verify_password(password: str, password_record: str) -> bool:
        salt, expected_hash = password_record.split("$", maxsplit=1)
        actual_hash = AuthService._hash_password(password, salt)
        return hmac.compare_digest(actual_hash, expected_hash)

    @staticmethod
    def register(payload: RegisterRequest) -> dict:
        AuthService._load_persisted_auth()

        if payload.email in store.users_by_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        student_id = payload.student_id
        if not student_id:
            # Backward-compat fallback for older clients/tests; UI now enforces explicit student ID.
            student_id = payload.email.split("@", 1)[0]

        student_id = AuthService._normalize_student_id(student_id)
        if student_id in store.users_by_student_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student ID already registered")

        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "student_id": student_id,
            "username": student_id,
            "name": payload.name,
            "email": payload.email,
            "password": AuthService._create_password_record(payload.password),
            "education_level": payload.education_level,
            "current_skills": payload.current_skills,
            "target_role": payload.target_role,
            "learning_goals": payload.learning_goals,
        }

        store.users_by_id[user_id] = user
        store.users_by_email[payload.email] = user
        store.users_by_student_id[student_id] = user
        AuthService._persist_auth()
        return user

    @staticmethod
    def login(payload: LoginRequest) -> tuple[str, dict]:
        AuthService._load_persisted_auth()

        user = None
        if payload.username:
            student_id = AuthService._normalize_student_id(payload.username)
            user = store.users_by_student_id.get(student_id)
        elif payload.email:
            user = store.users_by_email.get(payload.email)

        if not user or not AuthService._verify_password(payload.password, user["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username/email or password")

        token = uuid.uuid4().hex
        store.sessions[token] = user["id"]
        AuthService._persist_auth()
        return token, user

    @staticmethod
    def get_user_by_token(token: str) -> dict:
        AuthService._load_persisted_auth()

        user_id: Optional[str] = store.sessions.get(token)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        user = store.users_by_id.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User session invalid")
        return user

    @staticmethod
    def update_profile(user: dict, payload: ProfileUpdateRequest) -> dict:
        AuthService._load_persisted_auth()

        updates = payload.model_dump(exclude_unset=True)

        if "target_role" in updates and updates["target_role"] is not None:
            role = updates["target_role"]
            if role not in store.career_paths:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown career role")

        for key, value in updates.items():
            user[key] = value

        AuthService._persist_auth()
        return user
