from __future__ import annotations

from backend.admin.admin_service import AdminService


def admin_login(payload) -> dict:
    return AdminService.login(payload.username, payload.password)


def create_role(payload) -> dict:
    return AdminService.create_role(payload.model_dump())


def update_role(role_id: str, payload) -> dict:
    return AdminService.update_role(role_id, payload.model_dump(exclude_unset=True))


def delete_role(role_id: str) -> dict:
    return AdminService.delete_role(role_id)


def create_question(payload) -> dict:
    return AdminService.create_question(payload.model_dump())


def update_question(question_id: str, payload) -> dict:
    return AdminService.update_question(question_id, payload.model_dump(exclude_unset=True))


def delete_question(question_id: str) -> dict:
    return AdminService.delete_question(question_id)


def list_questions() -> dict:
    return AdminService.list_questions()


def create_custom_test(payload) -> dict:
    return AdminService.create_custom_test(payload.model_dump())


def assign_roadmap(payload) -> dict:
    return AdminService.assign_roadmap(payload.model_dump())


def upsert_role_roadmap_override(payload) -> dict:
    return AdminService.upsert_role_roadmap_override(payload.model_dump())


def get_students_analytics() -> dict:
    return AdminService.get_students_analytics()


def get_admin_snapshot() -> dict:
    return AdminService.get_admin_snapshot()
