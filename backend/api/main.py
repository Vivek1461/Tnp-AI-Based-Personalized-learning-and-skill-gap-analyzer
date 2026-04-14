from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.routes.assessment_routes import router as assessment_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.career_routes import router as career_router
from backend.routes.skill_gap_routes import router as skill_gap_router
from backend.routes.resume_routes import router as resume_router
from backend.routes.role_routes import router as role_router
from backend.routes.roadmap_routes import router as roadmap_router
from backend.routes.progress_routes import router as progress_router
from backend.admin.admin_routes import router as admin_router

app = FastAPI(
    title="AI Skill Gap Analyzer API",
    version="2.0.0",
    description="AI-powered personalized learning & skill gap analyzer for TNP platforms.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files if directory exists
_frontend_path = Path(__file__).parent.parent.parent / "frontend"
if _frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(_frontend_path), html=True), name="frontend")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app")


@app.get("/dashboard")
def dashboard_page() -> RedirectResponse:
    return RedirectResponse(url="/app/dashboard.html")


@app.get("/assessment")
def assessment_page() -> RedirectResponse:
    return RedirectResponse(url="/app/assessment.html")


@app.get("/roadmap")
def roadmap_page() -> RedirectResponse:
    return RedirectResponse(url="/app/roadmap.html")


@app.get("/resume")
def resume_page() -> RedirectResponse:
    return RedirectResponse(url="/app/resume.html")


@app.get("/admin")
def admin_page() -> RedirectResponse:
    return RedirectResponse(url="/app/admin.html")


@app.get("/index.html")
def legacy_home_page() -> RedirectResponse:
    return RedirectResponse(url="/")


@app.get("/dashboard.html")
def legacy_dashboard_page() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/assessment.html")
def legacy_assessment_page() -> RedirectResponse:
    return RedirectResponse(url="/assessment")


@app.get("/roadmap.html")
def legacy_roadmap_page() -> RedirectResponse:
    return RedirectResponse(url="/roadmap")


@app.get("/resume.html")
def legacy_resume_page() -> RedirectResponse:
    return RedirectResponse(url="/resume")


@app.get("/admin.html")
def legacy_admin_page() -> RedirectResponse:
    return RedirectResponse(url="/admin")


# ── Register all routers ─────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(career_router)
app.include_router(assessment_router)
app.include_router(skill_gap_router)
app.include_router(resume_router)
app.include_router(role_router)
app.include_router(roadmap_router)
app.include_router(progress_router)
app.include_router(admin_router)
