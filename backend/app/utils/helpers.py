"""Shared helpers: slugs, list parsing, deterministic hashing, skill categories."""

import ast
import hashlib
import json
import re
import uuid
from typing import Any, Optional

TECH_VOCAB = {
    "python", "java", "c++", "c", "c#", "javascript", "typescript", "sql", "mysql", "postgresql",
    "mongodb", "neo4j", "redis", "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
    "fastapi", "flask", "django", "react", "node.js", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "spark", "hadoop", "tableau", "power bi", "excel", "opencv", "spring boot",
}

_CATEGORY_RULES = [
    ("Programming", {"python", "java", "c++", "c", "c#", "javascript", "typescript", "go", "rust", "kotlin", "r", "scala"}),
    ("Databases", {"sql", "mysql", "postgresql", "mongodb", "neo4j", "redis", "nosql", "database", "dbms"}),
    ("Cloud & DevOps", {"aws", "azure", "gcp", "docker", "kubernetes", "git", "linux", "devops", "terraform", "ci/cd"}),
    ("ML & AI", {"machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn", "opencv", "yolov8", "ai", "computer vision"}),
    ("Data", {"pandas", "numpy", "tableau", "power bi", "excel", "statistics", "spark", "hadoop", "etl", "analytics", "data analysis"}),
    ("Web & APIs", {"react", "node.js", "django", "flask", "fastapi", "html", "css", "rest", "api", "spring"}),
]


def slugify(text: Any) -> str:
    return re.sub(r"[^a-z0-9+#]+", "-", str(text).lower()).strip("-")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def stable_hash(*parts: Any) -> int:
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest(), 16)


def clean(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return "" if s.lower() in {"nan", "none", "null"} else s


def dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for it in items:
        key = it.lower()
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def split_list(value: Any) -> list[str]:
    """Parse a list stored as JSON, a Python repr, or delimited text (| ; ,)."""
    s = clean(value)
    if not s:
        return []
    if s[0] in "[(":
        parsed = None
        try:
            parsed = json.loads(s)
        except Exception:
            try:
                parsed = ast.literal_eval(s)
            except Exception:
                parsed = None
        if isinstance(parsed, (list, tuple)):
            return dedupe([str(x).strip() for x in parsed if str(x).strip()])
        s = s.strip("[]()")
    parts = [s]
    for sep in ("|", ";", ","):
        if sep in s:
            parts = s.split(sep)
            break
    return dedupe([p.strip().strip("'\"") for p in parts if p.strip().strip("'\"")])


def parse_years(text: Any) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", clean(text), re.I)
    return float(m.group(1)) if m else None


def categorize_skill(name: str) -> str:
    low = name.lower()
    tokens = set(re.split(r"[^a-z0-9+#./]+", low))
    for category, keys in _CATEGORY_RULES:
        for k in keys:
            if (" " in k and k in low) or (" " not in k and k in tokens):
                return category
    return "General"


def skill_rows(names: list[str]) -> list[dict]:
    return [{"id": "SK-" + slugify(n), "name": n, "category": categorize_skill(n)} for n in dedupe(names)]