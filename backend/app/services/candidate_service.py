"""Candidate CRUD and read models (Neo4j + Mongo for emotion summary)."""

import logging

from app.database.mongodb import get_collection
from app.schemas.candidate import CandidateCreate
from app.services.shared import best_role, candidate_skill_map, interviewed_roles, role_requirements, run
from app.utils.errors import ConflictError, NotFoundError
from app.utils.helpers import new_id, skill_rows

logger = logging.getLogger(__name__)


def _exists(cid: str) -> bool:
    return bool(run("MATCH (c:Candidate {candidate_id:$id}) RETURN c.candidate_id AS id", id=cid))


def list_candidates(q=None, domain=None, job_type=None) -> dict:
    rows = run("""
        MATCH (c:Candidate)
        OPTIONAL MATCH (c)-[:ANSWERED]->(a:Answer)
        WITH c, avg(a.score) AS avg_score, count(a) AS answers
        RETURN c.candidate_id AS candidate_id, c.name AS name, c.domain AS domain,
               c.education AS education, c.experience_years AS experience_years,
               c.job_type AS job_type, avg_score, answers
        ORDER BY candidate_id
    """)
    smap, reqs, roles = candidate_skill_map(), role_requirements(), interviewed_roles()
    items = []
    for r in rows:
        skills = smap.get(r["candidate_id"], {}).get("skills", [])
        primary = best_role(skills, reqs, roles.get(r["candidate_id"]))
        overall = best_role(skills, reqs)
        items.append({
            **r, "skills": skills,
            "avg_score": round(r["avg_score"], 2) if r["avg_score"] is not None else None,
            "primary_role": primary["title"] if primary else None,
            "skill_coverage": primary["coverage"] if primary else 0,
            "best_role": overall["title"] if overall else None,
            "best_role_compat": overall["coverage"] if overall else 0,
        })
    facets = {
        "domains": sorted({i["domain"] for i in items if i["domain"]}),
        "job_types": sorted({i["job_type"] for i in items if i["job_type"]}),
    }
    if q:
        ql = q.lower()
        items = [i for i in items if ql in " ".join(
            [str(i["candidate_id"]), str(i["name"]), str(i["education"] or ""), " ".join(i["skills"])]).lower()]
    if domain:
        items = [i for i in items if i["domain"] == domain]
    if job_type:
        items = [i for i in items if i["job_type"] == job_type]
    return {"items": items, "total": len(items), "facets": facets}


def get_candidate(cid: str) -> dict:
    base = run("""
        MATCH (c:Candidate {candidate_id:$id})
        RETURN c.candidate_id AS candidate_id, c.name AS name, c.email AS email, c.education AS education,
               c.domain AS domain, c.experience_years AS experience_years, c.job_type AS job_type,
               c.experience_text AS experience_text
    """, id=cid)
    if not base:
        raise NotFoundError(f"Candidate {cid} not found")
    skills = [r["name"] for r in run(
        "MATCH (:Candidate {candidate_id:$id})-[:HAS_SKILL]->(s:Skill) RETURN s.name AS name ORDER BY name", id=cid)]
    rounds = run("""
        MATCH (:Candidate {candidate_id:$id})-[:PARTICIPATES_IN]->(r:InterviewRound)
        OPTIONAL MATCH (a:Answer {round_id:r.round_id})
        RETURN r.round_id AS round_id, r.round_label AS round_label, r.round_number AS round_number,
               r.date AS date, r.target_role AS target_role, count(a) AS answers
        ORDER BY round_number
    """, id=cid)
    answers = run("""
        MATCH (:Candidate {candidate_id:$id})-[:ANSWERED]->(a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
        OPTIONAL MATCH (a)-[:DEMONSTRATES]->(s:Skill)
        RETURN a.answer_id AS answer_id, a.round_id AS round_id, a.score AS score, q.question_id AS question_id,
               q.text AS question, q.difficulty AS difficulty, q.category AS category,
               collect(DISTINCT s.name) AS skills
        ORDER BY round_id, question_id
    """, id=cid)
    scores = [a["score"] for a in answers if a["score"] is not None]
    try:
        emotions = list(get_collection("emotion_logs").aggregate([
            {"$match": {"candidate_id": cid}},
            {"$group": {"_id": "$label", "count": {"$sum": 1}, "avg_confidence": {"$avg": "$confidence"}}},
            {"$project": {"_id": 0, "label": "$_id", "count": 1, "avg_confidence": {"$round": ["$avg_confidence", 2]}}},
            {"$sort": {"count": -1}},
        ]))
    except Exception as exc:
        logger.warning("Emotion summary unavailable: %s", exc)
        emotions = []
    return {
        "candidate": base[0], "skills": skills, "rounds": rounds, "answers": answers, "emotions": emotions,
        "stats": {"avg_score": round(sum(scores) / len(scores), 2) if scores else None,
                  "answers": len(answers), "rounds": len(rounds)},
    }


def _set_skills(cid: str, skills: list[str]) -> None:
    run("MATCH (:Candidate {candidate_id:$id})-[h:HAS_SKILL]->() DELETE h", id=cid)
    rows = skill_rows(skills)
    if rows:
        run("""
            MATCH (c:Candidate {candidate_id:$id})
            UNWIND $rows AS r
            MERGE (s:Skill {skill_id:r.id}) ON CREATE SET s.name=r.name, s.category=r.category
            MERGE (c)-[:HAS_SKILL]->(s)
        """, id=cid, rows=rows)
    run("MATCH (c:Candidate {candidate_id:$id}) SET c.skills=$skills", id=cid, skills=[r["name"] for r in rows])


def create_candidate(p: CandidateCreate) -> dict:
    cid = p.candidate_id or new_id("C")
    if _exists(cid):
        raise ConflictError(f"Candidate {cid} already exists")
    run("""
        CREATE (c:Candidate {candidate_id:$id, name:$name, email:$email, education:$education,
                             domain:$domain, job_type:$job_type, experience_years:$exp})
    """, id=cid, name=p.name, email=p.email, education=p.education, domain=p.domain,
        job_type=p.job_type, exp=p.experience_years)
    _set_skills(cid, p.skills)
    return get_candidate(cid)


def update_candidate(cid: str, data: dict) -> dict:
    if not _exists(cid):
        raise NotFoundError(f"Candidate {cid} not found")
    skills = data.pop("skills", None)
    if data:
        props = {("experience_years" if k == "experience_years" else k): v for k, v in data.items()}
        run("MATCH (c:Candidate {candidate_id:$id}) SET c += $props", id=cid, props=props)
    if skills is not None:
        _set_skills(cid, skills)
    return get_candidate(cid)


def delete_candidate(cid: str) -> dict:
    if not _exists(cid):
        raise NotFoundError(f"Candidate {cid} not found")
    run("MATCH (e:Emotion {candidate_id:$id}) DETACH DELETE e", id=cid)
    run("MATCH (a:Answer {candidate_id:$id}) OPTIONAL MATCH (a)-[:RECEIVED]->(f:Feedback) DETACH DELETE f, a", id=cid)
    run("MATCH (r:InterviewRound {candidate_id:$id}) DETACH DELETE r", id=cid)
    run("MATCH (c:Candidate {candidate_id:$id}) DETACH DELETE c", id=cid)
    mongo = {"interviews": 0, "emotion_logs": 0}
    try:
        mongo["interviews"] = get_collection("raw_interviews").delete_many({"candidate_id": cid}).deleted_count
        mongo["emotion_logs"] = get_collection("emotion_logs").delete_many({"candidate_id": cid}).deleted_count
    except Exception as exc:
        logger.warning("Mongo cleanup skipped: %s", exc)
    return {"deleted": cid, "mongo_removed": mongo}