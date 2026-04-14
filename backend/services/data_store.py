from __future__ import annotations

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List


# ── Load question bank from external JSON ─────────────────────────────────────
_QB_PATH = Path(__file__).parent / "question_bank.json"

def _load_question_bank() -> Dict[str, List[dict]]:
    try:
        with open(_QB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ── Unified Skill Taxonomy (alias → canonical name) ───────────────────────────
SKILL_TAXONOMY: Dict[str, str] = {
    # Python aliases
    "python3": "Python", "py": "Python", "pandas": "Python",
    "numpy": "Python", "matplotlib": "Python", "flask": "Python",
    "fastapi": "Python", "django": "Python", "scipy": "Python",
    # SQL aliases
    "postgres": "SQL", "postgresql": "SQL", "mysql": "SQL",
    "sqlite": "SQL", "sql server": "SQL", "mssql": "SQL",
    "database": "SQL", "db": "SQL", "oracle": "SQL",
    # ML aliases
    "sklearn": "Machine Learning", "scikit-learn": "Machine Learning",
    "scikit learn": "Machine Learning", "ml": "Machine Learning",
    "machine learning": "Machine Learning", "random forest": "Machine Learning",
    "xgboost": "Machine Learning", "gradient boosting": "Machine Learning",
    # Deep Learning aliases
    "tensorflow": "Deep Learning", "keras": "Deep Learning",
    "pytorch": "Deep Learning", "torch": "Deep Learning",
    "neural network": "Deep Learning", "cnn": "Deep Learning",
    "rnn": "Deep Learning", "lstm": "Deep Learning",
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    # DSA aliases
    "algorithms": "Data Structures & Algorithms",
    "data structures": "Data Structures & Algorithms",
    "dsa": "Data Structures & Algorithms",
    "leetcode": "Data Structures & Algorithms",
    "competitive programming": "Data Structures & Algorithms",
    # Statistics aliases
    "stats": "Statistics", "statistical analysis": "Statistics",
    "probability": "Statistics", "regression analysis": "Statistics",
    # Data Visualization aliases
    "seaborn": "Data Visualization", "plotly": "Data Visualization",
    "tableau": "Data Visualization", "power bi": "Data Visualization",
    "data visualization": "Data Visualization", "viz": "Data Visualization",
    # JavaScript aliases
    "js": "JavaScript", "es6": "JavaScript", "typescript": "JavaScript",
    "node": "Node.js", "nodejs": "Node.js", "node.js": "Node.js",
    # Web frameworks
    "reactjs": "React", "react.js": "React",
    "html5": "HTML", "html": "HTML",
    "css3": "CSS", "css": "CSS",
    # Cloud
    "aws": "Cloud Platform", "gcp": "Cloud Platform",
    "azure": "Cloud Platform", "cloud": "Cloud Platform",
    "serverless": "Cloud Platform",
    # Docker / K8s
    "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "docker": "Docker", "containers": "Docker",
    # Java
    "java ee": "Java", "j2ee": "Java",
    "spring": "Spring Boot", "springboot": "Spring Boot",
    # Excel
    "microsoft excel": "Excel", "spreadsheet": "Excel",
    "google sheets": "Excel",
    # Linux
    "unix": "Linux", "bash": "Linux", "shell scripting": "Linux",
    # APIs
    "api": "REST APIs", "rest": "REST APIs", "graphql": "REST APIs",
    "postman": "REST APIs",
    # Security
    "penetration testing": "Security Tools", "pen testing": "Security Tools",
    "network security": "Networking",
}


def normalize_skill(raw: str) -> str:
    """Map a raw skill string to its canonical taxonomy name."""
    key = raw.strip().lower()
    return SKILL_TAXONOMY.get(key, raw.strip().title())


class InMemoryDataStore:
    """Extended in-memory store for the full AI Skill Gap Analyzer platform."""

    def __init__(self) -> None:
        # Auth
        self.users_by_id: Dict[str, dict] = {}
        self.users_by_email: Dict[str, dict] = {}
        self.users_by_student_id: Dict[str, dict] = {}
        self.sessions: Dict[str, str] = {}

        # Assessment results: user_id → {skill: score}
        self.assessment_results: Dict[str, Dict[str, int]] = {}

        # Adaptive assessment sessions: user_id → session state dict
        self.assessment_sessions: Dict[str, dict] = {}

        # Resume parsed data cache: user_id → parsed_resume_dict
        self.resume_data: Dict[str, dict] = {}

        # Optional per-user role override (set by admin interventions)
        self.user_target_roles: Dict[str, str] = {}

        # Roadmap progress: user_id → {skill: {stage: bool}}
        self.roadmap_progress: Dict[str, Dict[str, Dict[str, bool]]] = {}

        # ── Admin auth / sessions ───────────────────────────────────────────
        # Default admin: username=tnp_admin, password=admin123 (override with env vars)
        self.admin_users_by_username: Dict[str, dict] = {}
        self.admin_sessions: Dict[str, str] = {}

        # ── Admin-controlled catalog (single source of truth) ──────────────
        self.admin_companies: Dict[str, dict] = {}
        self.admin_roles: Dict[str, dict] = {}
        self.admin_role_index: Dict[str, str] = {}  # "company::role" -> role_id

        # Role skills used by assessment/gap/resume/roadmap generators
        # shape: company -> role -> {skill: {weight_label, required_score, priority_value}}
        self.company_role_requirements: Dict[str, Dict[str, dict]] = {}

        # Admin-managed question catalog + custom tests
        self.admin_questions: Dict[str, dict] = {}
        self.admin_custom_tests: Dict[str, dict] = {}
        self.admin_role_test_assignments: Dict[str, List[str]] = {}
        self.admin_student_test_assignments: Dict[str, List[str]] = {}

        # Roadmap controls
        self.admin_role_roadmap_overrides: Dict[str, dict] = {}  # role -> roadmap template
        self.admin_student_roadmap_assignments: Dict[str, dict] = {}  # user_id -> roadmap payload

        # Intervention controls
        self.admin_student_resource_recommendations: Dict[str, List[dict]] = {}

        # ── Career Paths (skill → required score 0–100) ──────────────────────
        self.career_paths: Dict[str, Dict[str, int]] = {
            "Data Scientist": {
                "Python": 80, "Statistics": 85, "Machine Learning": 75,
                "Data Visualization": 70, "SQL": 70,
                "Data Structures & Algorithms": 60,
            },
            "ML Engineer": {
                "Python": 85, "Machine Learning": 85, "Deep Learning": 75,
                "Statistics": 70, "SQL": 65,
                "Data Structures & Algorithms": 75,
            },
            "Data Analyst": {
                "SQL": 85, "Excel": 80, "Python": 70,
                "Data Visualization": 80, "Statistics": 75,
            },
            "Software Engineer": {
                "Python": 80, "Data Structures & Algorithms": 85,
                "SQL": 70, "REST APIs": 75, "JavaScript": 70,
            },
            "AI Engineer": {
                "Python": 85, "Machine Learning": 80, "Deep Learning": 80,
                "Statistics": 75, "Data Structures & Algorithms": 70,
            },
            "Web Developer": {
                "HTML": 80, "CSS": 75, "JavaScript": 85, "React": 70, "REST APIs": 70,
            },
            "Java Backend Developer": {
                "Java": 85, "Spring Boot": 75, "SQL": 70,
                "System Design": 65, "REST APIs": 80,
            },
            "Cloud Engineer": {
                "Linux": 75, "Networking": 70, "Docker": 75,
                "Kubernetes": 70, "Cloud Platform": 80,
            },
            "DevOps Engineer": {
                "Linux": 80, "Docker": 80, "Kubernetes": 75,
                "CI/CD": 75, "Cloud Platform": 70,
            },
            "Full Stack Developer": {
                "HTML": 75, "CSS": 70, "JavaScript": 85,
                "Node.js": 75, "SQL": 65, "React": 70,
            },
            "Cybersecurity Analyst": {
                "Networking": 80, "Linux": 75, "Python": 65,
                "Security Tools": 80, "Cryptography": 70,
            },
        }

        # ── Question Bank (loaded from JSON) ─────────────────────────────────
        self.question_bank: Dict[str, List[dict]] = _load_question_bank()

        self._seed_admin_defaults()

    @staticmethod
    def _hash_admin_password(password: str, salt: str) -> str:
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return digest.hex()

    def _seed_admin_defaults(self) -> None:
        admin_username = os.getenv("ADMIN_USERNAME", "tnp_admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        salt = os.urandom(16).hex()
        hashed = self._hash_admin_password(admin_password, salt)
        self.admin_users_by_username[admin_username] = {
            "username": admin_username,
            "name": "TNP Head",
            "password": f"{salt}${hashed}",
        }

        # Seed company-role requirements from current career paths so admin panel
        # can manage existing behavior without breaking backward compatibility.
        default_company = "Campus_Default"
        self.company_role_requirements[default_company] = {}
        for role, skill_map in self.career_paths.items():
            normalized = {}
            for skill, required in skill_map.items():
                weight = "High" if required >= 80 else "Medium" if required >= 65 else "Low"
                normalized[skill] = {
                    "weight_label": weight,
                    "required_score": int(required),
                    "priority_value": 3 if weight == "High" else 2 if weight == "Medium" else 1,
                }
            self.company_role_requirements[default_company][role] = normalized


store = InMemoryDataStore()
