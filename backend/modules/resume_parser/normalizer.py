from __future__ import annotations

from typing import List

# Alias → canonical name map (lowercase aliases)
ALIAS_MAP: dict[str, str] = {
    # Python
    "py": "Python", "python3": "Python", "python2": "Python",
    # Machine Learning
    "ml": "Machine Learning", "machine learning": "Machine Learning",
    "scikit-learn": "Machine Learning", "sklearn": "Machine Learning",
    # Deep Learning
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    "tensorflow": "Deep Learning", "keras": "Deep Learning",
    "pytorch": "Deep Learning", "neural network": "Deep Learning",
    # JavaScript
    "js": "JavaScript", "es6": "JavaScript", "es2015": "JavaScript",
    "ecmascript": "JavaScript",
    # React
    "reactjs": "React", "react.js": "React",
    # Node
    "nodejs": "Node.js", "node": "Node.js",
    # SQL
    "mysql": "SQL", "postgres": "SQL", "postgresql": "SQL",
    "sqlite": "SQL", "mssql": "SQL",
    # Data Visualization
    "tableau": "Data Visualization", "power bi": "Data Visualization",
    "matplotlib": "Data Visualization", "seaborn": "Data Visualization",
    "plotly": "Data Visualization",
    # Cloud
    "aws": "Cloud Platform", "azure": "Cloud Platform",
    "gcp": "Cloud Platform", "google cloud": "Cloud Platform",
    # Linux
    "unix": "Linux", "bash": "Linux", "shell scripting": "Linux",
    # CI/CD
    "jenkins": "CI/CD", "github actions": "CI/CD", "gitlab ci": "CI/CD",
    "circleci": "CI/CD",
    # Misc
    "spring": "Spring Boot", "spring framework": "Spring Boot",
    "restful api": "REST APIs", "rest api": "REST APIs",
    "k8s": "Kubernetes",
    "pandas": "Pandas", "numpy": "NumPy",
    "mongo": "MongoDB", "nosql": "MongoDB",
    "figma": "UI/UX Design",
    "github": "Git", "gitlab": "Git",
}


def normalize(skills: List[str]) -> List[str]:
    """
    Map each skill in the list to its canonical name using the alias map.
    De-duplicate and preserve order.
    """
    seen: set[str] = set()
    normalized: List[str] = []
    for raw in skills:
        key = raw.strip().lower()
        canonical = ALIAS_MAP.get(key, raw.strip())
        # Title-case unknown skills for consistency
        if canonical == raw.strip():
            canonical = raw.strip().title()
        if canonical not in seen:
            seen.add(canonical)
            normalized.append(canonical)
    return normalized
