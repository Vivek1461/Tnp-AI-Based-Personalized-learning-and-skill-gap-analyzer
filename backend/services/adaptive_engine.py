from __future__ import annotations

"""
Adaptive Assessment Engine
--------------------------
Implements question-by-question adaptive difficulty logic:
- Starts at medium difficulty
- Correct answer → escalate toward hard
- Wrong answer  → drop toward easy
- Per-skill tracking; balanced question selection
"""

import random
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from backend.services.data_store import store


# Difficulty ordering
_DIFFICULTY_ORDER = ["easy", "medium", "hard"]
_DIFFICULTY_IDX = {d: i for i, d in enumerate(_DIFFICULTY_ORDER)}


def _next_difficulty(current: str, was_correct: bool) -> str:
    idx = _DIFFICULTY_IDX.get(current, 1)
    if was_correct:
        idx = min(idx + 1, 2)   # escalate
    else:
        idx = max(idx - 1, 0)   # drop
    return _DIFFICULTY_ORDER[idx]


def _build_skill_pool(role: str) -> Dict[str, List[dict]]:
    """Return {skill: [questions]} filtered to the role's required skills."""
    required_skills = list(store.career_paths.get(role, {}).keys())
    pool: Dict[str, List[dict]] = {}
    for skill in required_skills:
        # Try exact match, then case-insensitive
        qs = store.question_bank.get(skill) or next(
            (v for k, v in store.question_bank.items() if k.lower() == skill.lower()),
            []
        )
        if qs:
            pool[skill] = list(qs)  # copy
    return pool


def start_adaptive_session(user: dict) -> dict:
    """
    Initialise an adaptive session for the user's target role.
    Returns the first question (medium difficulty from first skill).

    Session state stored in store.assessment_sessions[user_id]:
    {
        "role": str,
        "skill_pool": {skill: [question_dicts]},
        "skill_queue": [skills remaining],
        "current_skill_idx": int,
        "difficulty": str,           # current difficulty
        "answered": {q_id: bool},    # qid → was_correct
        "skill_points": {skill: [earned, max]},
        "done": bool,
    }
    """
    role = user.get("target_role")
    if not role:
        raise HTTPException(status_code=400, detail="Set target_role before starting assessment")

    pool = _build_skill_pool(role)
    if not pool:
        raise HTTPException(status_code=404, detail="No questions found for this role")

    # Shuffle skill order
    skills = list(pool.keys())
    random.shuffle(skills)

    session: dict = {
        "role": role,
        "skill_pool": pool,
        "skill_queue": skills,
        "current_skill_idx": 0,
        "difficulty": "medium",
        "answered": {},
        "skill_points": {s: [0.0, 0.0] for s in skills},
        "questions_per_skill": 3,   # target 3 questions per skill
        "skill_q_count": {s: 0 for s in skills},
        "asked_ids": set(),
        "done": False,
    }

    store.assessment_sessions[user["id"]] = session

    q = _pick_next_question(session)
    if q is None:
        raise HTTPException(status_code=404, detail="Could not find a starting question")

    return _format_question_response(q, session, is_first=True)


def get_next_question(user: dict) -> dict:
    """Return next question for running session (no answer submission)."""
    session = store.assessment_sessions.get(user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="No active session. Call /api/assessment/adaptive/start first.")
    if session.get("done"):
        return _finalize_session(user, session)
    q = _pick_next_question(session)
    if q is None:
        return _finalize_session(user, session)
    return _format_question_response(q, session)


def submit_adaptive_answer(user: dict, question_id: str, selected: List[int]) -> dict:
    """
    Submit answer for one question.
    Returns: { correct, explanation, next_question OR results_if_done }
    """
    session = store.assessment_sessions.get(user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    if session.get("done"):
        return _finalize_session(user, session)

    # Look up question
    q_obj = _find_question(session, question_id)
    if not q_obj:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not in session")

    skill = q_obj["skill"]
    correct_answers: List[int] = q_obj.get("correct_answers", [])
    weight = q_obj.get("weight", 1)
    q_type = q_obj.get("type", "single_mcq")

    # Score this answer
    max_pts = weight * 100.0
    earned = _score_answer(q_type, selected, correct_answers, max_pts)
    was_correct = earned >= max_pts * 0.5

    # Update skill points
    session["skill_points"][skill][0] += earned
    session["skill_points"][skill][1] += max_pts
    session["answered"][question_id] = was_correct
    session["skill_q_count"][skill] = session["skill_q_count"].get(skill, 0) + 1

    # Adapt difficulty for next step
    session["difficulty"] = _next_difficulty(session["difficulty"], was_correct)

    # Check if done
    total_answered = len(session["answered"])
    max_q = len(session["skill_queue"]) * session["questions_per_skill"]
    if total_answered >= max_q:
        session["done"] = True
        final = _finalize_session(user, session)
        return {
            "correct": was_correct,
            "correct_answers": correct_answers,
            **final,
        }

    # Advance skill if quota met
    cur_skill = session["skill_queue"][session["current_skill_idx"]]
    if session["skill_q_count"].get(cur_skill, 0) >= session["questions_per_skill"]:
        next_idx = session["current_skill_idx"] + 1
        if next_idx >= len(session["skill_queue"]):
            session["done"] = True
            final = _finalize_session(user, session)
            return {"correct": was_correct, "correct_answers": correct_answers, **final}
        session["current_skill_idx"] = next_idx

    next_q = _pick_next_question(session)
    if next_q is None:
        session["done"] = True
        final = _finalize_session(user, session)
        return {"correct": was_correct, "correct_answers": correct_answers, **final}

    return {
        "correct": was_correct,
        "correct_answers": correct_answers,
        "next_question": _format_question_response(next_q, session),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _pick_next_question(session: dict) -> Optional[dict]:
    skill_queue = session["skill_queue"]
    idx = session["current_skill_idx"]
    if idx >= len(skill_queue):
        return None
    skill = skill_queue[idx]
    difficulty = session["difficulty"]
    pool = session["skill_pool"].get(skill, [])

    # Filter by difficulty, not yet asked
    candidates = [
        q for q in pool
        if q.get("difficulty") == difficulty
        and q["id"] not in session["asked_ids"]
    ]

    # Fallback: any difficulty not yet asked
    if not candidates:
        candidates = [q for q in pool if q["id"] not in session["asked_ids"]]

    if not candidates:
        return None

    # Prefer medium first, then hard, then easy
    pref_order = ["medium", "hard", "easy"]
    for diff in pref_order:
        sub = [q for q in candidates if q.get("difficulty") == diff]
        if sub:
            candidates = sub
            break

    q = random.choice(candidates)
    session["asked_ids"].add(q["id"])
    return q


def _find_question(session: dict, q_id: str) -> Optional[dict]:
    for qs in session["skill_pool"].values():
        for q in qs:
            if q["id"] == q_id:
                return q
    return None


def _score_answer(q_type: str, selected: List[int], correct: List[int], max_pts: float) -> float:
    if q_type in ("single_mcq", "case_based"):
        if selected and selected[0] in correct:
            return max_pts
        elif selected:
            return 0.0  # wrong, no negative
        return 0.0

    elif q_type == "multi_mcq":
        if not selected or not correct:
            return 0.0
        earn = 0.0
        for idx in selected:
            if idx in correct:
                earn += 1
            else:
                earn -= 0.5
        ratio = max(earn / len(correct), 0.0)
        return ratio * max_pts

    return 0.0


def _format_question_response(q: dict, session: dict, is_first: bool = False) -> dict:
    skill_queue = session["skill_queue"]
    total_q = len(skill_queue) * session["questions_per_skill"]
    answered_count = len(session["answered"])
    return {
        "question": {
            "id": q["id"],
            "skill": q["skill"],
            "type": q["type"],
            "prompt": q["prompt"],
            "options": q.get("options", []),
            "difficulty": q.get("difficulty", "medium"),
            "weight": q.get("weight", 1),
        },
        "progress": {
            "answered": answered_count,
            "total": total_q,
            "percent": round((answered_count / total_q) * 100) if total_q else 0,
            "current_difficulty": session["difficulty"],
        },
        "done": False,
    }


def _finalize_session(user: dict, session: dict) -> dict:
    from backend.services.assessment_service import AssessmentService

    skill_scores: Dict[str, dict] = {}
    total_earned = 0.0
    total_max = 0.0

    for skill, (earned, max_pts) in session["skill_points"].items():
        if max_pts == 0:
            continue
        score = round((earned / max_pts) * 100)
        score = max(0, min(100, score))
        skill_scores[skill] = {
            "score": score,
            "level": AssessmentService._get_level(score),
        }
        total_earned += earned
        total_max += max_pts

    overall = round((total_earned / total_max) * 100) if total_max else 0
    overall = max(0, min(100, overall))

    # Persist
    flat = {s: d["score"] for s, d in skill_scores.items()}
    store.assessment_results[user["id"]] = flat

    return {
        "done": True,
        "overall_score": overall,
        "target_role": session["role"],
        "skill_scores": skill_scores,
        "total_questions": len(session["answered"]),
    }
