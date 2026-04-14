from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

from backend.middleware.auth import get_current_user
from backend.modules.resume_parser.parser import extract_text
from backend.modules.resume_parser.skill_extractor import parse_resume
from backend.modules.resume_parser.normalizer import normalize
from backend.modules.resume_generator.generator import generate_pdf, generate_resume_json
from backend.services.data_store import store

router = APIRouter(prefix="/api/resume", tags=["resume"])


class ProjectInput(BaseModel):
    name: str
    description: str = ""
    tech: List[str] = []
    link: str = ""


class ExperienceInput(BaseModel):
    company: str
    role: str
    duration: str = ""
    bullets: List[str] = []


class ResumeGenerateRequest(BaseModel):
    projects: List[ProjectInput] = []
    experience: List[ExperienceInput] = []
    phone: str = ""
    linkedin: str = ""
    company: Optional[str] = None


@router.post("/parse")
async def parse_resume_endpoint(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> dict:
    """Upload a PDF or DOCX resume. Extracts and normalizes skills."""
    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if (
        file.content_type not in allowed_types
        and not file.filename.lower().endswith((".pdf", ".docx", ".doc"))
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported",
        )

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 5MB)",
        )

    text = extract_text(file.filename, file_bytes)
    parsed = parse_resume(text)
    normalized = normalize(parsed["skills"])

    resume_payload = {
        "name": parsed.get("name") or user.get("name"),
        "email": parsed.get("email") or user.get("email"),
        "education": parsed.get("education", []),
        "skills": parsed["skills"],
        "normalized_skills": normalized,
    }
    store.resume_data[user["id"]] = resume_payload

    # Merge into user's current_skills
    existing = set(user.get("current_skills", []))
    for skill in normalized:
        existing.add(skill)
    user["current_skills"] = list(existing)

    return {
        "message": "Resume parsed successfully",
        "name": resume_payload["name"],
        "email": resume_payload["email"],
        "education": resume_payload["education"],
        "skills": resume_payload["skills"],
        "normalized_skills": normalized,
        "skill_count": len(normalized),
    }


@router.post("/preview")
def preview_resume_endpoint(
    payload: ResumeGenerateRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Generate a structured JSON resume for frontend preview.
    Does NOT return a PDF — returns the resume as a JSON object so the
    frontend can render an HTML preview with a 'Regenerate' option.

    Body (all optional):
    {
        "projects": [{"name": ..., "description": ..., "tech": [...]}],
        "experience": [{"company": ..., "role": ..., "duration": ..., "bullets": [...]}],
        "phone": "...",
        "linkedin": "...",
        "company": "..."
    }
    """
    target_role = store.user_target_roles.get(user["id"]) or user.get("target_role")
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set a target role in your profile first",
        )

    resume_data = store.resume_data.get(user["id"], {})
    skills = resume_data.get("normalized_skills", user.get("current_skills", []))
    education = resume_data.get(
        "education",
        [user.get("education_level", "")] if user.get("education_level") else [],
    )
    email = resume_data.get("email") or user.get("email", "")
    name = resume_data.get("name") or user.get("name", "Student")
    required_skills = list(store.career_paths.get(target_role, {}).keys())

    student_data = {
        "name": name,
        "email": email,
        "phone": payload.phone,
        "linkedin": payload.linkedin,
        "skills": skills,
        "education": education,
        "projects": [p.dict() for p in payload.projects],
        "experience": [e.dict() for e in payload.experience],
    }

    resume_json = generate_resume_json(
        student_data=student_data,
        target_role=target_role,
        company=payload.company,
        required_skills=required_skills,
    )

    return {"status": "ok", "resume": resume_json}


@router.post("/generate")
def generate_resume_endpoint(
    payload: ResumeGenerateRequest,
    user: dict = Depends(get_current_user),
) -> Response:
    """
    Generate an ATS-friendly PDF resume.
    Accepts same optional body as /preview.
    Returns PDF as binary download.
    """
    target_role = store.user_target_roles.get(user["id"]) or user.get("target_role")
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set a target role first",
        )

    resume_data = store.resume_data.get(user["id"], {})
    skills = resume_data.get("normalized_skills", user.get("current_skills", []))
    education = resume_data.get(
        "education",
        [user.get("education_level", "")] if user.get("education_level") else [],
    )
    email = resume_data.get("email") or user.get("email", "")
    name = resume_data.get("name") or user.get("name", "Student")
    required_skills = list(store.career_paths.get(target_role, {}).keys())

    student_data = {
        "name": name,
        "email": email,
        "phone": payload.phone,
        "linkedin": payload.linkedin,
        "skills": skills,
        "education": education,
        "projects": [p.dict() for p in payload.projects],
        "experience": [e.dict() for e in payload.experience],
    }

    pdf_bytes = generate_pdf(
        student_data=student_data,
        target_role=target_role,
        company=payload.company,
        required_skills=required_skills,
    )

    if pdf_bytes[:4] == b"%PDF":
        media_type = "application/pdf"
        filename = f"{name.replace(' ', '_')}_Resume.pdf"
    else:
        media_type = "text/plain"
        filename = f"{name.replace(' ', '_')}_Resume.txt"

    return Response(
        content=pdf_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
