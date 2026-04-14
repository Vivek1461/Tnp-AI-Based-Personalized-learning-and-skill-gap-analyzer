from __future__ import annotations

import io
from typing import Any, Dict, List, Optional


# ── Role → relevant skill categories ─────────────────────────────────────────
_ROLE_SKILL_MAP: Dict[str, List[str]] = {
    "Data Analyst": [
        "SQL", "Excel", "Python", "Data Visualization", "Statistics",
        "Tableau", "Power BI", "Pandas", "NumPy",
    ],
    "Data Scientist": [
        "Python", "Machine Learning", "Statistics", "SQL",
        "Data Visualization", "Deep Learning", "Scikit-learn",
        "TensorFlow", "Feature Engineering",
    ],
    "ML Engineer": [
        "Python", "Machine Learning", "Deep Learning", "TensorFlow",
        "PyTorch", "Docker", "REST APIs", "SQL", "Statistics",
        "Data Structures & Algorithms",
    ],
    "AI Engineer": [
        "Python", "Deep Learning", "Machine Learning", "TensorFlow",
        "PyTorch", "Statistics", "Linear Algebra", "REST APIs",
    ],
    "Software Engineer": [
        "Python", "Data Structures & Algorithms", "SQL", "REST APIs",
        "JavaScript", "System Design", "Git", "Docker",
    ],
    "Web Developer": [
        "HTML", "CSS", "JavaScript", "React", "REST APIs", "Node.js",
    ],
    "Full Stack Developer": [
        "HTML", "CSS", "JavaScript", "React", "Node.js", "SQL",
        "REST APIs", "Docker",
    ],
    "Java Backend Developer": [
        "Java", "Spring Boot", "SQL", "REST APIs", "System Design",
        "Docker", "Microservices",
    ],
    "DevOps Engineer": [
        "Linux", "Docker", "Kubernetes", "CI/CD", "Cloud Platform",
        "Shell Scripting", "Python",
    ],
    "Cloud Engineer": [
        "Cloud Platform", "Docker", "Kubernetes", "Linux",
        "Networking", "Terraform", "CI/CD",
    ],
    "Cybersecurity Analyst": [
        "Networking", "Linux", "Python", "Security Tools",
        "Cryptography", "SQL",
    ],
}

# ── Role-specific AI-generated summaries ─────────────────────────────────────
_ROLE_SUMMARIES: Dict[str, str] = {
    "Data Analyst": (
        "Results-driven Data Analyst with strong proficiency in SQL, Excel, and Python. "
        "Experienced in transforming complex datasets into actionable business insights through "
        "data visualization and statistical analysis. Adept at building dashboards and reports "
        "that drive data-driven decision-making across cross-functional teams."
    ),
    "Data Scientist": (
        "Analytical Data Scientist skilled in machine learning, statistical modeling, and "
        "Python-based data pipelines. Experienced in developing predictive models that deliver "
        "measurable business value, with expertise in feature engineering, model evaluation, "
        "and communicating findings to non-technical stakeholders."
    ),
    "ML Engineer": (
        "Machine Learning Engineer with hands-on experience building, training, and deploying "
        "production-grade ML models using TensorFlow/PyTorch and Python. Proficient in designing "
        "scalable ML pipelines, containerizing models with Docker, and integrating them into "
        "REST APIs for real-world applications."
    ),
    "AI Engineer": (
        "AI Engineer passionate about developing intelligent systems using deep learning and "
        "natural language processing. Skilled in architecting end-to-end AI solutions from "
        "research to deployment, with strong foundations in mathematics, Python, and "
        "cloud-based model serving."
    ),
    "Software Engineer": (
        "Software Engineer with strong fundamentals in data structures, algorithms, and "
        "system design. Experienced in developing scalable backend services, RESTful APIs, "
        "and database solutions. Committed to writing clean, maintainable code following "
        "industry best practices."
    ),
    "Web Developer": (
        "Creative Web Developer proficient in building responsive, user-friendly web "
        "applications using modern JavaScript frameworks. Experienced in both frontend "
        "and API integration, with a strong eye for UI/UX and performance optimization."
    ),
    "Full Stack Developer": (
        "Full Stack Developer with end-to-end expertise in building web applications from "
        "database design to frontend delivery. Skilled in React, Node.js, SQL, and RESTful APIs, "
        "with experience deploying containerized applications to production environments."
    ),
    "Java Backend Developer": (
        "Backend Developer specializing in Java and Spring Boot microservices architecture. "
        "Experienced in designing RESTful APIs, database schema optimization, and building "
        "scalable enterprise applications with a focus on reliability and code quality."
    ),
    "DevOps Engineer": (
        "DevOps Engineer experienced in automating CI/CD pipelines, container orchestration "
        "with Kubernetes, and infrastructure-as-code practices. Skilled in bridging development "
        "and operations to deliver reliable, scalable systems with minimal downtime."
    ),
}

# ── Project enhancement templates ─────────────────────────────────────────────
_PROJECT_TEMPLATES: Dict[str, str] = {
    "ml": "Developed a {name} using {tech}, achieving {metric}% accuracy on {dataset} dataset with scikit-learn and Python",
    "web": "Built a full-stack {name} using {tech}, serving {users}+ users with real-time data updates and responsive design",
    "data": "Designed and implemented a {name} pipeline using {tech} that processed {volume} records and reduced reporting time by {pct}%",
    "api": "Architected and deployed a RESTful {name} API using {tech} with JWT authentication, rate limiting, and auto-generated documentation",
    "generic": "Developed {name} using {tech}, delivering {outcome} and demonstrating proficiency in end-to-end software development",
}

_ROLE_TOOLS_MAP: Dict[str, List[str]] = {
    "Data Analyst": ["Pandas", "NumPy", "Matplotlib", "Seaborn", "Tableau", "Power BI", "MS Excel", "PostgreSQL"],
    "Data Scientist": ["Pandas", "NumPy", "Scikit-learn", "TensorFlow", "Jupyter Notebook", "Matplotlib", "Git"],
    "ML Engineer": ["TensorFlow", "PyTorch", "Scikit-learn", "Docker", "FastAPI", "Git", "MLflow", "Kubernetes"],
    "AI Engineer": ["TensorFlow", "PyTorch", "Hugging Face", "FastAPI", "Docker", "Git", "CUDA"],
    "Software Engineer": ["Git", "Docker", "Postman", "VS Code", "PostgreSQL", "Redis", "Linux"],
    "Web Developer": ["React", "Node.js", "Git", "Webpack", "Figma", "Chrome DevTools"],
    "Full Stack Developer": ["React", "Node.js", "PostgreSQL", "Docker", "Git", "Postman", "Nginx"],
    "Java Backend Developer": ["Spring Boot", "Maven", "PostgreSQL", "Docker", "IntelliJ IDEA", "Git", "JUnit"],
    "DevOps Engineer": ["Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions", "Prometheus"],
    "Cloud Engineer": ["AWS", "GCP", "Terraform", "Docker", "Kubernetes", "CloudFormation", "Linux"],
}


def _filter_skills_for_role(skills: List[str], target_role: str, required_skills: Optional[List[str]] = None) -> List[str]:
    """Return skills ordered by role relevance — most important first."""
    role_relevant = _ROLE_SKILL_MAP.get(target_role, [])
    # Priority 1: in required_skills AND in role map
    # Priority 2: in role map
    # Priority 3: everything else
    req_set = set(s.lower() for s in (required_skills or []))
    role_set = set(s.lower() for s in role_relevant)
    skill_lower = {s.lower(): s for s in skills}

    tier1 = [skill_lower[k] for k in skill_lower if k in req_set and k in role_set]
    tier2 = [skill_lower[k] for k in skill_lower if k in role_set and k not in req_set]
    tier3 = [skill_lower[k] for k in skill_lower if k not in role_set and k not in req_set]
    return tier1 + tier2 + tier3


def _enhance_project(proj: Dict[str, Any], target_role: str) -> str:
    """Convert a raw project dict into a strong impact bullet point."""
    name = proj.get("name", "Project")
    tech = ", ".join(proj.get("tech", [])) or "Python"
    desc = proj.get("description", "").strip()

    # If desc already looks professional (>60 chars), use it
    if len(desc) > 60:
        return desc

    # Otherwise, generate enhanced description based on role
    role_lower = target_role.lower()
    if any(kw in role_lower for kw in ["ml", "ai", "data scien", "machine"]):
        return f"Developed {name} using {tech}, applying machine learning algorithms to extract insights and improve prediction accuracy by ~15-25%"
    elif any(kw in role_lower for kw in ["analyst", "analytics"]):
        return f"Built {name} using {tech}, enabling data-driven decisions through automated reporting and visualization dashboards"
    elif any(kw in role_lower for kw in ["web", "frontend", "full stack"]):
        return f"Designed and deployed {name} using {tech} with responsive UI, RESTful API integration, and optimized page load performance"
    elif any(kw in role_lower for kw in ["backend", "software", "engineer"]):
        return f"Engineered {name} using {tech} with scalable architecture, RESTful API endpoints, and comprehensive error handling"
    elif any(kw in role_lower for kw in ["devops", "cloud"]):
        return f"Automated {name} deployment pipeline using {tech}, reducing deployment time by 60% with containerization and CI/CD"
    else:
        return f"Developed {name} using {tech}, demonstrating end-to-end project delivery with real-world application"


def generate_resume_json(
    student_data: Dict[str, Any],
    target_role: str,
    company: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate a structured JSON resume (for preview / frontend rendering).
    """
    name = student_data.get("name", "Student Name")
    email = student_data.get("email", "student@example.com")
    phone = student_data.get("phone", "")
    linkedin = student_data.get("linkedin", "")
    skills: List[str] = student_data.get("skills", [])
    education: List[str] = student_data.get("education", [])
    projects: List[Dict] = student_data.get("projects", [])
    experience: List[Dict] = student_data.get("experience", [])

    # Filter & order skills
    ordered_skills = _filter_skills_for_role(skills, target_role, required_skills)

    # Tools
    role_tools = _ROLE_TOOLS_MAP.get(target_role, [])
    all_tools = list(dict.fromkeys(role_tools))  # deduplicated

    # Summary
    summary = _ROLE_SUMMARIES.get(target_role)
    if not summary:
        company_str = f" at {company}" if company else ""
        summary = (
            f"Motivated and detail-oriented student seeking a {target_role} role{company_str}. "
            f"Proficient in {', '.join(ordered_skills[:4] or ['relevant technologies'])} "
            f"with a strong foundation in software development principles and a passion for "
            f"building impactful solutions."
        )

    # Enhance projects
    enhanced_projects = []
    for p in projects:
        enhanced_projects.append({
            "name": p.get("name", "Project"),
            "tech": p.get("tech", []),
            "description": _enhance_project(p, target_role),
            "link": p.get("link", ""),
        })

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "target_role": target_role,
        "company": company,
        "summary": summary,
        "skills": ordered_skills,
        "tools": all_tools,
        "education": education,
        "experience": experience,
        "projects": enhanced_projects,
        "ats_keywords": list(set(ordered_skills + (required_skills or []))),
    }


def generate_pdf(
    student_data: Dict[str, Any],
    target_role: str,
    company: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
) -> bytes:
    """
    Generate an ATS-friendly resume PDF using reportlab.
    First builds structured JSON, then renders to PDF.
    """
    resume = generate_resume_json(student_data, target_role, company, required_skills)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=1.8*cm, bottomMargin=1.8*cm,
        )
        styles = getSampleStyleSheet()

        name_style = ParagraphStyle("name", fontSize=20, fontName="Helvetica-Bold",
                                    alignment=TA_CENTER, spaceAfter=3)
        contact_style = ParagraphStyle("contact", fontSize=9.5, fontName="Helvetica",
                                       alignment=TA_CENTER, spaceAfter=8, textColor=colors.HexColor("#374151"))
        section_style = ParagraphStyle("sec", fontSize=11, fontName="Helvetica-Bold",
                                       spaceAfter=4, spaceBefore=10,
                                       textColor=colors.HexColor("#1a1a2e"))
        body_style = ParagraphStyle("body", fontSize=9.5, fontName="Helvetica",
                                    spaceAfter=3, leading=14)
        bullet_style = ParagraphStyle("bullet", fontSize=9.5, fontName="Helvetica",
                                      leftIndent=14, spaceAfter=3, leading=13)
        job_title_style = ParagraphStyle("job", fontSize=10, fontName="Helvetica-Bold",
                                         spaceAfter=1)

        def section(title: str):
            return [
                Paragraph(title.upper(), section_style),
                HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4361ee")),
                Spacer(1, 5),
            ]

        story = []

        # ── Header ────────────────────────────────────────────────────────────
        story.append(Paragraph(resume["name"], name_style))
        contact_parts = [resume["email"]]
        if resume["phone"]:
            contact_parts.append(resume["phone"])
        if resume["linkedin"]:
            contact_parts.append(resume["linkedin"])
        story.append(Paragraph(" | ".join(contact_parts), contact_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4361ee")))
        story.append(Spacer(1, 6))

        # ── Professional Summary ──────────────────────────────────────────────
        story += section("Professional Summary")
        story.append(Paragraph(resume["summary"], body_style))

        # ── Technical Skills ──────────────────────────────────────────────────
        if resume["skills"]:
            story += section("Technical Skills")
            # Group into rows of ~5
            grouped = [resume["skills"][i:i+6] for i in range(0, len(resume["skills"]), 6)]
            for grp in grouped:
                story.append(Paragraph("• " + "  •  ".join(grp), body_style))

        # ── Tools & Technologies ──────────────────────────────────────────────
        if resume["tools"]:
            story += section("Tools & Technologies")
            story.append(Paragraph(" | ".join(resume["tools"][:12]), body_style))

        # ── Experience ────────────────────────────────────────────────────────
        if resume["experience"]:
            story += section("Experience")
            for exp in resume["experience"]:
                company_name = exp.get("company", "")
                role_title = exp.get("role", exp.get("title", ""))
                duration = exp.get("duration", "")
                header = f"<b>{role_title}</b> | {company_name}"
                if duration:
                    header += f" | {duration}"
                story.append(Paragraph(header, job_title_style))
                for bullet in exp.get("bullets", []):
                    story.append(Paragraph(f"• {bullet}", bullet_style))
                story.append(Spacer(1, 4))

        # ── Projects ─────────────────────────────────────────────────────────
        if resume["projects"]:
            story += section("Projects")
            for proj in resume["projects"]:
                p_name = proj.get("name", "Project")
                p_tech = ", ".join(proj.get("tech", []))
                tech_str = f" <font color='#4361ee'>[{p_tech}]</font>" if p_tech else ""
                story.append(Paragraph(f"<b>{p_name}</b>{tech_str}", body_style))
                if proj.get("description"):
                    story.append(Paragraph(f"• {proj['description']}", bullet_style))
                if proj.get("link"):
                    story.append(Paragraph(f"  🔗 {proj['link']}", bullet_style))
                story.append(Spacer(1, 4))

        # ── Education ─────────────────────────────────────────────────────────
        if resume["education"]:
            story += section("Education")
            for edu in resume["education"]:
                story.append(Paragraph(f"• {edu}", bullet_style))

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        return _generate_text_fallback(resume)


def _generate_text_fallback(resume: Dict[str, Any]) -> bytes:
    """Plain-text fallback if reportlab not installed."""
    lines = [
        resume["name"], resume["email"],
        f"Phone: {resume['phone']}" if resume["phone"] else "",
        "=" * 65, "",
        "PROFESSIONAL SUMMARY", "-" * 65,
        resume["summary"], "",
        "TECHNICAL SKILLS", "-" * 65,
        "  " + " | ".join(resume["skills"]), "",
    ]
    if resume["tools"]:
        lines += ["TOOLS & TECHNOLOGIES", "-" * 65, "  " + " | ".join(resume["tools"]), ""]
    if resume["experience"]:
        lines += ["EXPERIENCE", "-" * 65]
        for exp in resume["experience"]:
            lines.append(f"  {exp.get('role','')} @ {exp.get('company','')} ({exp.get('duration','')})")
            for b in exp.get("bullets", []):
                lines.append(f"    • {b}")
        lines.append("")
    if resume["projects"]:
        lines += ["PROJECTS", "-" * 65]
        for p in resume["projects"]:
            lines.append(f"  {p['name']}: {p.get('description','')}")
        lines.append("")
    if resume["education"]:
        lines += ["EDUCATION", "-" * 65]
        for e in resume["education"]:
            lines.append(f"  - {e}")
    return "\n".join(lines).encode("utf-8")
