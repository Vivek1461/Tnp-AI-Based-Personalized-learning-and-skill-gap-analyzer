from __future__ import annotations

import re
from typing import Dict, List, Optional


# ── Master skill list with regex patterns ───────────────────────────────────
# Format: canonical_name -> list of regex patterns (case-insensitive)
SKILL_PATTERNS: Dict[str, List[str]] = {
    "Python": [r"\bpython\b", r"\bpy\b"],
    "SQL": [r"\bsql\b", r"\bmysql\b", r"\bpostgresql\b", r"\bpostgres\b", r"\bsqlite\b"],
    "Java": [r"\bjava\b(?!script)"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b", r"\bes6\b", r"\bes2015\b"],
    "React": [r"\breact\.?js\b", r"\breact\b"],
    "Node.js": [r"\bnode\.?js\b", r"\bnode\b"],
    "HTML": [r"\bhtml\b", r"\bhtml5\b"],
    "CSS": [r"\bcss\b", r"\bcss3\b", r"\bsass\b", r"\bscss\b"],
    "Machine Learning": [r"\bmachine\s+learning\b", r"\bml\b", r"\bscikit[\s-]?learn\b"],
    "Deep Learning": [r"\bdeep\s+learning\b", r"\bdl\b", r"\bneural\s+network\b", r"\btensorflow\b", r"\bkeras\b", r"\bpytorch\b"],
    "Statistics": [r"\bstatistics\b", r"\bstatistical\b", r"\bstats\b"],
    "Linear Algebra": [r"\blinear\s+algebra\b", r"\bmatrix\b", r"\bvector\s+math\b"],
    "Data Visualization": [r"\bdata\s+visual", r"\bmatplotlib\b", r"\bseaborn\b", r"\btableau\b", r"\bpower\s*bi\b", r"\bplotly\b"],
    "Docker": [r"\bdocker\b", r"\bcontainer(?:ization)?\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "Cloud Platform": [r"\baws\b", r"\bazure\b", r"\bgcp\b", r"\bgoogle\s+cloud\b", r"\bcloud\s+platform\b"],
    "Linux": [r"\blinux\b", r"\bunix\b", r"\bbash\b", r"\bshell\s+scripting\b"],
    "Networking": [r"\bnetwork(?:ing)?\b", r"\btcp\b", r"\bip\b", r"\bdns\b"],
    "Spring Boot": [r"\bspring\s*boot\b", r"\bspring\s+framework\b"],
    "REST APIs": [r"\brest(?:ful)?\s*api\b", r"\bapi\s+design\b", r"\brestapi\b", r"\bapi\b"],
    "System Design": [r"\bsystem\s+design\b", r"\barchitecture\b"],
    "CI/CD": [r"\bci/?cd\b", r"\bjenkins\b", r"\bgithub\s+actions\b", r"\bgitlab\s+ci\b"],
    "Excel": [r"\bexcel\b", r"\bms\s*excel\b", r"\bspreadsheet\b"],
    "Security Tools": [r"\bburp\s+suite\b", r"\bnmap\b", r"\bwireshark\b", r"\bsecurity\s+tools\b", r"\bpenetration\s+test\b"],
    "Cryptography": [r"\bcryptography\b", r"\bencryption\b", r"\brsa\b", r"\baes\b"],
    "Kotlin": [r"\bkotlin\b"],
    "React Native": [r"\breact\s*native\b"],
    "UI/UX Design": [r"\bui[/\s]?ux\b", r"\bfigma\b", r"\buser\s+interface\b", r"\bux\s+design\b"],
    "Git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
    "MongoDB": [r"\bmongodb\b", r"\bmongo\b", r"\bnosql\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
}

# ── Section parsers ─────────────────────────────────────────────────────────

def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def _extract_name(text: str) -> Optional[str]:
    """Heuristic: first non-empty line that has at least 2 alphabetic words."""
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 1:
            words = [w for w in line.split() if w.isalpha()]
            if len(words) >= 2:
                return " ".join(words[:4])
    return None


def _extract_education(text: str) -> List[str]:
    edu_keywords = [
        r"b\.?tech", r"b\.?e\b", r"m\.?tech", r"b\.?sc", r"m\.?sc",
        r"bca", r"mca", r"bachelor", r"master", r"phd", r"diploma",
        r"engineering", r"computer\s+science", r"information\s+technology",
    ]
    found = []
    for line in text.splitlines():
        low = line.lower()
        for kw in edu_keywords:
            if re.search(kw, low):
                cleaned = line.strip()
                if cleaned and cleaned not in found:
                    found.append(cleaned)
                break
    return found[:5]  # limit to 5 education lines


def extract_skills_from_text(text: str) -> List[str]:
    """Return canonical skill names found in the text."""
    found = []
    low = text.lower()
    for canonical, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, low, re.IGNORECASE):
                if canonical not in found:
                    found.append(canonical)
                break
    return found


def parse_resume(text: str) -> dict:
    """
    Full resume parse: returns structured dict.

    Returns:
        {
            "name": str | None,
            "email": str | None,
            "education": [str],
            "skills": [str],   # canonical skill names
        }
    """
    return {
        "name": _extract_name(text),
        "email": _extract_email(text),
        "education": _extract_education(text),
        "skills": extract_skills_from_text(text),
    }
