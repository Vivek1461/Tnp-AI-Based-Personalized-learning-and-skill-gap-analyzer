from __future__ import annotations

import hashlib
import hmac
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from backend.modules.progress_tracker.tracker import compute_metrics
from backend.services.data_store import store
from backend.services.skill_gap_service import SkillGapService


WEIGHT_PRIORITY = {"High": 3, "Medium": 2, "Low": 1}
QUESTION_TYPE_MAP = {
    "MCQ": "single_mcq",
    "MULTI": "multi_mcq",
    "CASE": "case_based",
    "single_mcq": "single_mcq",
    "multi_mcq": "multi_mcq",
    "case_based": "case_based",
}


class AdminService:
    @staticmethod
    def _activity_rank(student_row: dict) -> tuple:
        # Higher tuple means the row is more likely to represent current activity.
        progress = student_row.get("roadmap_progress", {})
        assessment_count = len(student_row.get("assessment_scores", {}) or {})
        return (
            assessment_count,
            progress.get("completed_items", 0),
            progress.get("overall_completion_pct", 0),
            student_row.get("readiness_score", 0),
        )

    @staticmethod
    def _resolve_student_account(student_identifier: str) -> Optional[dict]:
        if not student_identifier:
            return None
        if student_identifier in store.users_by_id:
            return store.users_by_id.get(student_identifier)
        key = student_identifier.strip().upper().replace(" ", "")
        return store.users_by_student_id.get(key)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return digest.hex()

    @staticmethod
    def _verify_password(password: str, password_record: str) -> bool:
        try:
            salt, expected_hash = password_record.split("$", maxsplit=1)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Admin credential format invalid") from exc
        actual_hash = AdminService._hash_password(password, salt)
        return hmac.compare_digest(actual_hash, expected_hash)

    @staticmethod
    def login(username: str, password: str) -> dict:
        admin = store.admin_users_by_username.get(username)
        if not admin or not AdminService._verify_password(password, admin["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

        token = uuid.uuid4().hex
        store.admin_sessions[token] = username
        return {
            "access_token": token,
            "token_type": "bearer",
            "admin": {
                "username": admin["username"],
                "name": admin.get("name", "TNP Head"),
            },
        }

    @staticmethod
    def get_admin_by_token(token: str) -> dict:
        username = store.admin_sessions.get(token)
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired admin token")

        admin = store.admin_users_by_username.get(username)
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin session invalid")
        return admin

    @staticmethod
    def _refresh_role_index() -> None:
        store.admin_role_index = {}
        for role_id, role in store.admin_roles.items():
            key = f"{role['company'].strip().lower()}::{role['role'].strip().lower()}"
            store.admin_role_index[key] = role_id

    @staticmethod
    def _normalize_role_skills(skills: List[dict]) -> List[dict]:
        if not skills:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one skill requirement is required")

        normalized: List[dict] = []
        for item in skills:
            skill = str(item.get("skill", "")).strip()
            weight = str(item.get("weight", "Medium")).strip().title()
            min_score = int(item.get("minimum_score_required", 70))
            if not skill:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill name is required")
            if weight not in WEIGHT_PRIORITY:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weight must be High, Medium, or Low")
            if min_score < 0 or min_score > 100:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="minimum_score_required must be 0-100")
            normalized.append(
                {
                    "skill": skill,
                    "weight": weight,
                    "minimum_score_required": min_score,
                }
            )
        return normalized

    @staticmethod
    def _upsert_company_role_requirements(company: str, role: str, skills: List[dict]) -> None:
        company_bucket = store.company_role_requirements.setdefault(company, {})
        company_bucket[role] = {
            item["skill"]: {
                "weight_label": item["weight"],
                "required_score": item["minimum_score_required"],
                "priority_value": WEIGHT_PRIORITY[item["weight"]],
            }
            for item in skills
        }

    @staticmethod
    def _sync_career_paths(role: str, skills: List[dict]) -> None:
        # Keep legacy modules compatible by maintaining role -> {skill: required_score}
        store.career_paths[role] = {item["skill"]: item["minimum_score_required"] for item in skills}

    @staticmethod
    def create_role(payload: dict) -> dict:
        company = str(payload.get("company", "")).strip()
        role = str(payload.get("role", "")).strip()
        if not company or not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="company and role are required")

        skills = AdminService._normalize_role_skills(payload.get("skills", []))
        role_id = uuid.uuid4().hex

        role_data = {
            "id": role_id,
            "company": company,
            "role": role,
            "skills": skills,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        store.admin_roles[role_id] = role_data
        store.admin_companies.setdefault(company, {"name": company})

        AdminService._refresh_role_index()
        AdminService._upsert_company_role_requirements(company, role, skills)
        AdminService._sync_career_paths(role, skills)

        return role_data

    @staticmethod
    def update_role(role_id: str, payload: dict) -> dict:
        existing = store.admin_roles.get(role_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        company = str(payload.get("company", existing["company"]))
        role = str(payload.get("role", existing["role"]))
        skills = AdminService._normalize_role_skills(payload.get("skills", existing["skills"]))

        existing.update(
            {
                "company": company,
                "role": role,
                "skills": skills,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        store.admin_companies.setdefault(company, {"name": company})

        AdminService._refresh_role_index()
        AdminService._upsert_company_role_requirements(company, role, skills)
        AdminService._sync_career_paths(role, skills)
        return existing

    @staticmethod
    def delete_role(role_id: str) -> dict:
        existing = store.admin_roles.pop(role_id, None)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        company = existing["company"]
        role = existing["role"]
        if company in store.company_role_requirements:
            store.company_role_requirements[company].pop(role, None)
            if not store.company_role_requirements[company]:
                store.company_role_requirements.pop(company, None)
        store.career_paths.pop(role, None)

        AdminService._refresh_role_index()
        return {"deleted": True, "role_id": role_id, "company": company, "role": role}

    @staticmethod
    def _ensure_question_index() -> None:
        if store.admin_questions:
            return

        for skill, questions in store.question_bank.items():
            for q in questions:
                qid = str(q.get("id", uuid.uuid4().hex))
                q_copy = dict(q)
                q_copy["id"] = qid
                q_copy["skill"] = q_copy.get("skill", skill)
                store.admin_questions[qid] = q_copy

    @staticmethod
    def _rebuild_question_bank() -> None:
        grouped: Dict[str, List[dict]] = defaultdict(list)
        for question in store.admin_questions.values():
            grouped[question["skill"]].append(question)
        store.question_bank = dict(grouped)

    @staticmethod
    def create_question(payload: dict) -> dict:
        AdminService._ensure_question_index()

        prompt = str(payload.get("question", payload.get("prompt", "")).strip())
        skill = str(payload.get("skill", "")).strip()
        q_type_input = str(payload.get("type", "MCQ")).strip()
        q_type = QUESTION_TYPE_MAP.get(q_type_input, None)
        difficulty = str(payload.get("difficulty", "Medium")).strip().lower()
        weight = int(payload.get("weight", 1))

        if not prompt or not skill or not q_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question, skill and valid type are required")
        if difficulty not in {"easy", "medium", "hard", "expert"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="difficulty must be Easy, Medium, Hard, or Expert")
        if weight < 1 or weight > 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="weight must be between 1 and 10")

        qid = uuid.uuid4().hex
        question = {
            "id": qid,
            "skill": skill,
            "type": q_type,
            "prompt": prompt,
            "options": payload.get("options", []),
            "correct_answers": payload.get("correct_answers", []),
            "difficulty": difficulty,
            "weight": weight,
        }
        store.admin_questions[qid] = question
        AdminService._rebuild_question_bank()
        return question

    @staticmethod
    def update_question(question_id: str, payload: dict) -> dict:
        AdminService._ensure_question_index()

        existing = store.admin_questions.get(question_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        if "question" in payload:
            existing["prompt"] = str(payload["question"]).strip()
        if "prompt" in payload:
            existing["prompt"] = str(payload["prompt"]).strip()
        if "skill" in payload:
            existing["skill"] = str(payload["skill"]).strip()
        if "type" in payload:
            q_type = QUESTION_TYPE_MAP.get(str(payload["type"]).strip())
            if not q_type:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question type")
            existing["type"] = q_type
        if "difficulty" in payload:
            diff = str(payload["difficulty"]).strip().lower()
            if diff not in {"easy", "medium", "hard", "expert"}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="difficulty must be Easy, Medium, Hard, or Expert")
            existing["difficulty"] = diff
        if "weight" in payload:
            w = int(payload["weight"])
            if w < 1 or w > 10:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="weight must be between 1 and 10")
            existing["weight"] = w
        if "options" in payload:
            existing["options"] = payload["options"]
        if "correct_answers" in payload:
            existing["correct_answers"] = payload["correct_answers"]

        AdminService._rebuild_question_bank()
        return existing

    @staticmethod
    def delete_question(question_id: str) -> dict:
        AdminService._ensure_question_index()
        removed = store.admin_questions.pop(question_id, None)
        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        AdminService._rebuild_question_bank()
        return {"deleted": True, "question_id": question_id}

    @staticmethod
    def list_questions() -> dict:
        AdminService._ensure_question_index()
        return {"questions": list(store.admin_questions.values())}

    @staticmethod
    def create_custom_test(payload: dict) -> dict:
        name = str(payload.get("name", "")).strip()
        question_ids = payload.get("question_ids", [])
        role_id = payload.get("role_id")
        student_id = payload.get("student_id")
        resolved_student = AdminService._resolve_student_account(str(student_id).strip()) if student_id else None
        target_account_id = resolved_student["id"] if resolved_student else None
        target_student_id = resolved_student.get("student_id") if resolved_student else student_id

        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test name is required")
        if not question_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question_ids are required")

        AdminService._ensure_question_index()
        missing = [qid for qid in question_ids if qid not in store.admin_questions]
        if missing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown question ids: {missing}")

        test_id = uuid.uuid4().hex
        test = {
            "id": test_id,
            "name": name,
            "question_ids": question_ids,
            "role_id": role_id,
            "student_id": target_student_id,
            "student_account_id": target_account_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        store.admin_custom_tests[test_id] = test

        if role_id:
            bucket = store.admin_role_test_assignments.setdefault(role_id, [])
            if test_id not in bucket:
                bucket.append(test_id)
        if target_account_id:
            bucket = store.admin_student_test_assignments.setdefault(target_account_id, [])
            if test_id not in bucket:
                bucket.append(test_id)

        return test

    @staticmethod
    def assign_roadmap(payload: dict) -> dict:
        student_identifier = str(payload.get("student_id", "")).strip()
        if not student_identifier:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="student_id is required")

        resolved_student = AdminService._resolve_student_account(student_identifier)
        if not resolved_student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student account not found for provided student_id")
        account_id = resolved_student["id"]
        student_id = resolved_student.get("student_id", student_identifier)

        role = payload.get("role")
        if role:
            store.user_target_roles[account_id] = role

        assignment = {
            "student_id": student_id,
            "role": role,
            "timeline_weeks": int(payload.get("timeline_weeks", 8)),
            "difficulty_progression": payload.get("difficulty_progression", ["beginner", "intermediate", "advanced"]),
            "custom_steps": payload.get("custom_steps", []),
            "custom_resources": payload.get("custom_resources", []),
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }
        store.admin_student_roadmap_assignments[account_id] = assignment

        recommended = payload.get("recommended_resources", [])
        if recommended:
            store.admin_student_resource_recommendations[account_id] = recommended

        return assignment

    @staticmethod
    def upsert_role_roadmap_override(payload: dict) -> dict:
        role = str(payload.get("role", "")).strip()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="role is required")

        override = {
            "role": role,
            "timeline_weeks": int(payload.get("timeline_weeks", 8)),
            "difficulty_progression": payload.get("difficulty_progression", ["beginner", "intermediate", "advanced"]),
            "custom_steps": payload.get("custom_steps", []),
            "custom_resources": payload.get("custom_resources", []),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        store.admin_role_roadmap_overrides[role] = override
        return override

    @staticmethod
    def _resolve_user_role(user: dict) -> Optional[str]:
        return store.user_target_roles.get(user["id"]) or user.get("target_role")

    @staticmethod
    def get_students_analytics() -> dict:
        students: List[dict] = []
        students_by_identity: Dict[str, dict] = {}
        weak_skill_counter: Counter = Counter()
        role_readiness: Dict[str, List[int]] = defaultdict(list)
        performance_scores: List[int] = []

        for user in store.users_by_id.values():
            target_role = AdminService._resolve_user_role(user)
            assessment = store.assessment_results.get(user["id"], {})
            resume = store.resume_data.get(user["id"], {})
            progress_metrics = compute_metrics(user["id"])

            readiness = 0
            gaps: List[dict] = []
            if target_role and assessment:
                try:
                    gap_result = SkillGapService.analyze({**user, "target_role": target_role})
                    readiness = int(gap_result.get("readiness_percent", 0))
                    gaps = gap_result.get("gaps", [])
                except HTTPException:
                    readiness = 0

            for g in gaps:
                weak_skill_counter[g.get("skill", "Unknown")] += 1

            if target_role:
                role_readiness[target_role].append(readiness)

            student_row = {
                "student_id": user.get("student_id", user["id"]),
                "account_id": user["id"],
                "name": user.get("name", "Student"),
                "email": user.get("email", ""),
                "target_role": target_role,
                "resume_skills": resume.get("normalized_skills", user.get("current_skills", [])),
                "assessment_scores": assessment,
                "skill_gaps": gaps,
                "roadmap_progress": progress_metrics,
                "readiness_score": readiness,
                "assigned_test_ids": store.admin_student_test_assignments.get(user["id"], []),
                "assigned_roadmap": store.admin_student_roadmap_assignments.get(user["id"]),
                "recommended_resources": store.admin_student_resource_recommendations.get(user["id"], []),
            }

            identity_key = str(student_row["student_id"]).strip().upper()
            existing = students_by_identity.get(identity_key)
            if not existing or AdminService._activity_rank(student_row) > AdminService._activity_rank(existing):
                students_by_identity[identity_key] = student_row

            if assessment:
                performance_scores.extend(list(assessment.values()))

        students = list(students_by_identity.values())

        # Rebuild aggregate counters from deduplicated rows only.
        weak_skill_counter = Counter()
        role_readiness = defaultdict(list)
        performance_scores = []
        for row in students:
            for g in row.get("skill_gaps", []):
                weak_skill_counter[g.get("skill", "Unknown")] += 1
            if row.get("target_role"):
                role_readiness[row["target_role"]].append(int(row.get("readiness_score", 0)))
            scores = row.get("assessment_scores", {})
            if scores:
                performance_scores.extend(list(scores.values()))

        avg_perf = round(sum(performance_scores) / len(performance_scores), 2) if performance_scores else 0
        role_wise = {
            role: round(sum(scores) / len(scores), 2) if scores else 0
            for role, scores in role_readiness.items()
        }

        return {
            "students": students,
            "aggregates": {
                "student_count": len(students),
                "average_performance": avg_perf,
                "most_common_weak_skills": [
                    {"skill": skill, "count": count}
                    for skill, count in weak_skill_counter.most_common(10)
                ],
                "role_wise_readiness": role_wise,
            },
        }

    @staticmethod
    def get_admin_snapshot() -> dict:
        AdminService._ensure_question_index()
        return {
            "companies": sorted(store.company_role_requirements.keys()),
            "roles": list(store.admin_roles.values()),
            "questions": list(store.admin_questions.values()),
            "custom_tests": list(store.admin_custom_tests.values()),
            "role_roadmap_overrides": list(store.admin_role_roadmap_overrides.values()),
            "student_roadmap_assignments": list(store.admin_student_roadmap_assignments.values()),
        }
