"""Role compatibility, skill-gap analysis and similar candidates (transparent set arithmetic)."""

from app.services.shared import candidate_skill_map, coverage, jaccard, role_requirements
from app.utils.errors import NotFoundError

LABEL = "System-generated role compatibility (skill overlap), not a hiring decision."


def _candidate(cid: str) -> dict:
    c = candidate_skill_map().get(cid)
    if not c:
        raise NotFoundError(f"Candidate {cid} not found")
    return c


def role_recommendations(cid: str) -> dict:
    cand = _candidate(cid)
    roles = []
    for r in role_requirements():
        names = [x["name"] for x in r["required"]]
        roles.append({"role_id": r["role_id"], "title": r["title"], "required": names,
                      **coverage(cand["skills"], names)})
    roles.sort(key=lambda x: -x["coverage"])
    return {"candidate_id": cid, "name": cand["name"], "label": LABEL, "roles": roles}


def skill_gap(cid: str, role_id: str) -> dict:
    cand = _candidate(cid)
    role = next((r for r in role_requirements() if r["role_id"] == role_id or r["title"] == role_id), None)
    if not role:
        raise NotFoundError(f"Role {role_id} not found")
    names = [x["name"] for x in role["required"]]
    return {"candidate_id": cid, "role": {"role_id": role["role_id"], "title": role["title"]},
            "required": names, **coverage(cand["skills"], names)}


def similar_candidates(cid: str, limit: int = 5) -> dict:
    cand = _candidate(cid)
    out = []
    for oid, o in candidate_skill_map().items():
        if oid == cid:
            continue
        shared, pct = jaccard(cand["skills"], o["skills"])
        if shared:
            out.append({"candidate_id": oid, "name": o["name"], "domain": o["domain"],
                        "shared_skills": shared, "similarity": pct})
    out.sort(key=lambda x: -x["similarity"])
    return {"candidate_id": cid, "method": "Jaccard similarity over HAS_SKILL relationships", "items": out[:limit]}