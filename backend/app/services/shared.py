"""Shared graph helpers used by several services."""

from typing import Any

from app.database.neo4j import run_cypher


def run(query: str, **params: Any) -> list[dict]:
    return run_cypher(query, params)


def candidate_skill_map() -> dict[str, dict]:
    rows = run("""
        MATCH (c:Candidate)
        OPTIONAL MATCH (c)-[:HAS_SKILL]->(s:Skill)
        RETURN c.candidate_id AS id, c.name AS name, c.domain AS domain, collect(s.name) AS skills
    """)
    return {r["id"]: r for r in rows}


def role_requirements() -> list[dict]:
    return run("""
        MATCH (r:Role)
        OPTIONAL MATCH (s:Skill)-[rel:REQUIRED_FOR]->(r)
        WITH r, s, rel ORDER BY rel.weight DESC
        RETURN r.role_id AS role_id, r.title AS title, r.department AS department,
               collect(CASE WHEN s IS NULL THEN NULL ELSE {name: s.name, weight: rel.weight} END) AS required
        ORDER BY title
    """)


def interviewed_roles() -> dict[str, list[str]]:
    rows = run(
        "MATCH (c:Candidate)-[:INTERVIEWED_FOR]->(r:Role) "
        "RETURN c.candidate_id AS id, collect(r.title) AS roles"
    )
    return {r["id"]: r["roles"] for r in rows}


def coverage(candidate_skills: list[str], required_names: list[str]) -> dict:
    have = {s.lower() for s in candidate_skills}
    matched = [n for n in required_names if n.lower() in have]
    missing = [n for n in required_names if n.lower() not in have]
    pct = round(100 * len(matched) / len(required_names), 1) if required_names else 0.0
    return {
        "matched": matched,
        "missing": missing,
        "coverage": pct
    }


def jaccard(a: list[str], b: list[str]) -> tuple[list[str], float]:
    sa, sb = {s.lower(): s for s in a}, {s.lower(): s for s in b}
    shared = [sa[k] for k in sa if k in sb]
    union = len(set(sa) | set(sb))
    return shared, round(100 * len(shared) / union, 1) if union else 0.0


def best_role(
    cand_skills: list[str],
    reqs: list[dict],
    prefer: list[str] | None = None
) -> dict | None:
    pool = [r for r in reqs if prefer and r["title"] in prefer] or reqs

    best = None

    for r in pool:
        names = [x["name"] for x in r["required"]]
        cov = coverage(cand_skills, names)

        if best is None or cov["coverage"] > best["coverage"]:
            best = {
                "role_id": r["role_id"],
                "title": r["title"],
                "required": names,
                **cov
            }

    return best