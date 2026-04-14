from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from backend.services.data_store import store


class AssessmentService:
    """
    Enhanced assessment engine:
    - Real MCQ / multi-correct / case-based questions
    - Weighted scoring per skill
    - Returns skill-wise competency with level labels
    """

    LEVEL_THRESHOLDS = [
        (80, "Advanced"),
        (60, "Intermediate"),
        (40, "Beginner"),
        (0, "Novice"),
    ]

    @staticmethod
    def _get_level(score: float) -> str:
        for threshold, label in AssessmentService.LEVEL_THRESHOLDS:
            if score >= threshold:
                return label
        return "Novice"

    @staticmethod
    def _build_question_lookup() -> Dict[str, dict]:
        q_lookup: Dict[str, dict] = {}
        for skill_qs in store.question_bank.values():
            for q in skill_qs:
                q_lookup[q["id"]] = q
        return q_lookup

    @staticmethod
    def _resolve_assigned_questions(user: dict, role: str) -> List[dict]:
        q_lookup = AssessmentService._build_question_lookup()
        selected_ids: List[str] = []

        # Highest priority: student-specific test assignment
        student_test_ids = list(store.admin_student_test_assignments.get(user["id"], []))
        if user.get("student_id"):
            student_test_ids.extend(store.admin_student_test_assignments.get(user["student_id"], []))
        for test_id in student_test_ids:
            test = store.admin_custom_tests.get(test_id)
            if test:
                selected_ids.extend(test.get("question_ids", []))

        # Role-level test assignment
        for role_id, role_data in store.admin_roles.items():
            if role_data.get("role") != role:
                continue
            for test_id in store.admin_role_test_assignments.get(role_id, []):
                test = store.admin_custom_tests.get(test_id)
                if test:
                    selected_ids.extend(test.get("question_ids", []))

        if not selected_ids:
            return []

        # Deduplicate while preserving order
        seen = set()
        questions = []
        for qid in selected_ids:
            if qid in seen or qid not in q_lookup:
                continue
            seen.add(qid)
            q = q_lookup[qid]
            questions.append(
                {
                    "id": q["id"],
                    "skill": q.get("skill", "General"),
                    "type": q.get("type", "single_mcq"),
                    "prompt": q.get("prompt", ""),
                    "options": q.get("options", []),
                    "difficulty": q.get("difficulty", "medium"),
                    "weight": q.get("weight", 1),
                }
            )
        return questions

    @staticmethod
    def start_assessment(user: dict) -> dict:
        role = store.user_target_roles.get(user["id"]) or user.get("target_role")
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Set target_role in profile before starting assessment",
            )

        required_skills = store.career_paths.get(role)
        if not required_skills:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career role not found")

        assigned_questions = AssessmentService._resolve_assigned_questions(user, role)
        if assigned_questions:
            return {"target_role": role, "questions": assigned_questions, "source": "admin_assigned_test"}

        questions = []
        for skill in required_skills:
            skill_qs = store.question_bank.get(skill, [])
            if skill_qs:
                for q in skill_qs[:2]:  # max 2 questions per skill
                    questions.append({
                        "id": q["id"],
                        "skill": q.get("skill", skill),
                        "type": q["type"],
                        "prompt": q["prompt"],
                        "options": q.get("options", []),
                        "difficulty": q.get("difficulty", "medium"),
                        "weight": q.get("weight", 1),
                        # NOTE: correct_answers NOT included in response (server-side only)
                    })
            else:
                # Generic placeholder question
                questions.append({
                    "id": f"generic-{skill.lower().replace(' ', '-')}",
                    "skill": skill,
                    "type": "single_mcq",
                    "prompt": f"Rate your current proficiency in {skill} (select the best fit).",
                    "options": [
                        "I have no experience with this",
                        "I understand the basics",
                        "I have working experience",
                        "I am proficient / can teach it",
                    ],
                    "difficulty": "easy",
                    "weight": 1,
                })

        return {"target_role": role, "questions": questions}

    @staticmethod
    def evaluate_answers(user: dict, answers: Dict[str, List[int]]) -> dict:
        """
        Evaluate submitted answers against the question bank.

        answers: { question_id: [selected_option_indices] }

        Returns:
        {
            "overall_score": int,
            "skill_scores": {
                "Python": {"score": 85, "level": "Advanced"},
                ...
            }
        }
        """
        # Build question lookup
        q_lookup = AssessmentService._build_question_lookup()

        # Accumulate scores per skill: {skill: (earned_points, max_points)}
        skill_points: Dict[str, List[float]] = {}  # {skill: [earned, max]}

        for q_id, selected in answers.items():
            q = q_lookup.get(q_id)
            if not q:
                continue

            skill = q.get("skill", "Unknown")
            weight = q.get("weight", 1)
            correct: List[int] = q.get("correct_answers", [])
            q_type = q.get("type", "single_mcq")

            if skill not in skill_points:
                skill_points[skill] = [0.0, 0.0]

            max_pts = weight * 100
            skill_points[skill][1] += max_pts

            if q_type == "single_mcq" or q_type == "case_based":
                # Full credit if correct, -25 penalty if wrong
                if selected and selected[0] in correct:
                    skill_points[skill][0] += max_pts
                elif selected:
                    skill_points[skill][0] += max(-0.25 * max_pts, 0)  # no negative total

            elif q_type == "multi_mcq":
                # Partial credit: for each correct selection +1, for each wrong -1
                if not selected:
                    continue
                num_options = len(q.get("options", []))
                earn = 0.0
                for idx in range(num_options):
                    should_select = idx in correct
                    did_select = idx in selected
                    if should_select and did_select:
                        earn += 1
                    elif not should_select and did_select:
                        earn -= 0.5  # wrong selection penalty
                ratio = max(earn / len(correct), 0.0) if correct else 0.0
                skill_points[skill][0] += ratio * max_pts

        # Handle generic self-assessment questions
        # Map option index → score range
        _generic_score_map = {0: 5, 1: 35, 2: 65, 3: 90}
        for q_id, selected in answers.items():
            if not q_id.startswith("generic-"):
                continue
            # Derive skill from id: generic-python -> Python
            skill_token = q_id.replace("generic-", "").replace("-", " ").title()
            # Find canonical skill name
            matched_skill = None
            for s in store.career_paths.get(user.get("target_role", ""), {}):
                if s.lower() == skill_token.lower():
                    matched_skill = s
                    break
            if not matched_skill:
                matched_skill = skill_token
            if matched_skill not in skill_points:
                skill_points[matched_skill] = [0.0, 100.0]
            idx = selected[0] if selected else 0
            skill_points[matched_skill][0] += _generic_score_map.get(idx, 0)

        # Calculate per-skill scores
        skill_scores: Dict[str, dict] = {}
        total_earned = 0.0
        total_max = 0.0

        for skill, (earned, max_pts) in skill_points.items():
            score = round((earned / max_pts) * 100) if max_pts else 0
            score = max(0, min(100, score))
            skill_scores[skill] = {
                "score": score,
                "level": AssessmentService._get_level(score),
            }
            total_earned += earned
            total_max += max_pts

        overall_score = round((total_earned / total_max) * 100) if total_max else 0
        overall_score = max(0, min(100, overall_score))

        # Persist flat scores for skill gap analysis
        flat_scores = {skill: data["score"] for skill, data in skill_scores.items()}
        store.assessment_results[user["id"]] = flat_scores

        return {
            "user_id": user["id"],
            "target_role": user.get("target_role"),
            "overall_score": overall_score,
            "skill_scores": skill_scores,
        }

    @staticmethod
    def submit_assessment(user: dict, payload: Any) -> dict:
        """Legacy: direct score submission (for compatibility with existing test)."""
        validated_scores = {}
        for skill, score in payload.scores.items():
            if score < 0 or score > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Score for {skill} must be between 0 and 100",
                )
            validated_scores[skill] = score

        store.assessment_results[user["id"]] = validated_scores

        skill_scores = {
            skill: {"score": score, "level": AssessmentService._get_level(score)}
            for skill, score in validated_scores.items()
        }
        overall = round(sum(validated_scores.values()) / len(validated_scores)) if validated_scores else 0

        return {
            "user_id": user["id"],
            "target_role": user.get("target_role"),
            "overall_score": overall,
            "skill_scores": skill_scores,
            "scores": validated_scores,  # backward compat for existing tests
        }

    @staticmethod
    def get_assessment_result(user: dict) -> dict:
        result = store.assessment_results.get(user["id"])
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assessment result found")

        skill_scores = {
            skill: {"score": score, "level": AssessmentService._get_level(score)}
            for skill, score in result.items()
        }
        overall = round(sum(result.values()) / len(result)) if result else 0

        return {
            "user_id": user["id"],
            "target_role": user.get("target_role"),
            "overall_score": overall,
            "skill_scores": skill_scores,
            "scores": result,  # legacy flat scores for backward compat
        }
