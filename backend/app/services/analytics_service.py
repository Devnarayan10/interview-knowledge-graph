"""Neo4j analytics, GDS algorithms (with graceful fallback) and MongoDB aggregations."""

import logging

from app.database.mongodb import get_collection
from app.services.shared import candidate_skill_map, jaccard, run
from app.utils.errors import BadRequestError

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ dashboard
def dashboard_summary() -> dict:
    labels = {r["l"]: r["c"] for r in run("MATCH (n) RETURN labels(n)[0] AS l, count(*) AS c")}
    rels = run("MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
    avg = run("MATCH (a:Answer) RETURN round(avg(a.score), 2) AS v")[0]["v"]
    mongo = {"interviews": 0, "emotion_logs": 0, "available": True}
    emotion_dist: list = []
    try:
        mongo["interviews"] = get_collection("raw_interviews").count_documents({})
        mongo["emotion_logs"] = get_collection("emotion_logs").count_documents({})
        emotion_dist = mongo_aggregations()["emotion_distribution"]
    except Exception as exc:
        logger.warning("MongoDB unavailable for dashboard: %s", exc)
        mongo["available"] = False
    charts = {
        "candidates_by_domain": run("MATCH (c:Candidate) RETURN coalesce(c.domain,'Unknown') AS name, count(*) AS value ORDER BY value DESC"),
        "questions_by_difficulty": run("MATCH (q:Question) RETURN coalesce(q.difficulty,'Unknown') AS name, count(*) AS value ORDER BY value DESC"),
        "role_distribution": run("MATCH (c:Candidate)-[:INTERVIEWED_FOR]->(r:Role) RETURN r.title AS name, count(DISTINCT c) AS value ORDER BY value DESC"),
        "skill_distribution": run("MATCH (c:Candidate)-[:HAS_SKILL]->(s:Skill) RETURN s.name AS name, count(DISTINCT c) AS value ORDER BY value DESC LIMIT 12"),
        "score_by_role": run("MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q:Question) RETURN coalesce(q.target_role,'Unknown') AS name, round(avg(a.score), 2) AS value ORDER BY value DESC"),
        "rounds_per_candidate": run("MATCH (c:Candidate)-[:PARTICIPATES_IN]->(r:InterviewRound) RETURN c.candidate_id AS name, count(r) AS value ORDER BY value DESC, name LIMIT 15"),
        "emotion_distribution": [{"name": e["label"], "value": e["count"]} for e in emotion_dist],
    }
    counts = {
        "candidates": labels.get("Candidate", 0), "questions": labels.get("Question", 0),
        "answers": labels.get("Answer", 0), "skills": labels.get("Skill", 0), "roles": labels.get("Role", 0),
        "companies": labels.get("Company", 0), "technologies": labels.get("Technology", 0),
        "rounds": labels.get("InterviewRound", 0), "relationships": rels,
        "interviews": mongo["interviews"], "emotion_logs": mongo["emotion_logs"],
    }
    return {"counts": counts, "avg_score": avg, "mongodb_available": mongo["available"], "charts": charts}


# ------------------------------------------------------------------ neo4j analytics
def overview() -> dict:
    return {
        "avg_score": run("MATCH (a:Answer) RETURN round(avg(a.score), 2) AS v")[0]["v"],
        "top_candidates": run("""
            MATCH (c:Candidate)-[:ANSWERED]->(a:Answer)
            RETURN c.candidate_id AS candidate_id, c.name AS name, round(avg(a.score), 2) AS avg_score, count(a) AS answers
            ORDER BY avg_score DESC LIMIT 5"""),
        "category_performance": run("""
            MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
            RETURN coalesce(q.category,'Unknown') AS name, round(avg(a.score), 2) AS avg_score, count(a) AS count
            ORDER BY avg_score DESC"""),
        "domain_performance": run("""
            MATCH (c:Candidate)-[:ANSWERED]->(a:Answer)
            RETURN coalesce(c.domain,'Unknown') AS name, round(avg(a.score), 2) AS avg_score, count(DISTINCT c) AS candidates
            ORDER BY avg_score DESC"""),
    }


def skills_analytics(skill: str | None = None) -> dict:
    top = run("""
        MATCH (s:Skill)
        OPTIONAL MATCH (c:Candidate)-[:HAS_SKILL]->(s)
        WITH s, count(DISTINCT c) AS candidates
        OPTIONAL MATCH (q:Question)-[:TESTS_SKILL]->(s)
        WITH s, candidates, count(DISTINCT q) AS questions
        OPTIONAL MATCH (s)-[:REQUIRED_FOR]->(r:Role)
        WITH s, candidates, questions, count(DISTINCT r) AS roles
        OPTIONAL MATCH (a:Answer)-[:DEMONSTRATES]->(s)
        RETURN s.name AS name, s.category AS category, candidates, questions, roles,
               count(DISTINCT a) AS evidence, round(avg(a.score), 2) AS avg_score
        ORDER BY candidates + questions DESC, name""")
    cooc = run("""
        MATCH (q:Question)-[:TESTS_SKILL]->(a:Skill), (q)-[:TESTS_SKILL]->(b:Skill)
        WHERE a.skill_id < b.skill_id
        RETURN a.name AS a, b.name AS b, count(DISTINCT q) AS count ORDER BY count DESC LIMIT 15""")
    out = {"top_skills": top, "cooccurrence": cooc, "strongest": []}
    if skill:
        out["strongest"] = run("""
            MATCH (c:Candidate)-[:ANSWERED]->(a:Answer)-[:DEMONSTRATES]->(s:Skill)
            WHERE toLower(s.name) = toLower($skill)
            RETURN c.candidate_id AS candidate_id, c.name AS name, round(avg(a.score), 2) AS avg_score, count(a) AS evidence
            ORDER BY avg_score DESC, evidence DESC LIMIT 10""", skill=skill)
    return out


def roles_analytics() -> dict:
    return {"roles": run("""
        MATCH (r:Role)
        OPTIONAL MATCH (s:Skill)-[:REQUIRED_FOR]->(r)
        WITH r, count(DISTINCT s) AS required_skills
        OPTIONAL MATCH (q:Question)-[:FOR_ROLE]->(r)
        WITH r, required_skills, count(DISTINCT q) AS questions
        OPTIONAL MATCH (c:Candidate)-[:INTERVIEWED_FOR]->(r)
        WITH r, required_skills, questions, count(DISTINCT c) AS candidates
        OPTIONAL MATCH (a:Answer)-[:IN_RESPONSE_TO]->(:Question)-[:FOR_ROLE]->(r)
        RETURN r.title AS title, r.department AS department, required_skills, questions, candidates,
               round(avg(a.score), 2) AS avg_score
        ORDER BY title""")}


def difficulties_analytics() -> dict:
    return {
        "by_difficulty": run("""
            MATCH (q:Question) OPTIONAL MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q)
            RETURN coalesce(q.difficulty,'Unknown') AS difficulty, count(DISTINCT q) AS questions,
                   count(a) AS answers, round(avg(a.score), 2) AS avg_score ORDER BY difficulty"""),
        "hardest": run("""
            MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
            WITH q, avg(a.score) AS avg_score, count(a) AS answers
            RETURN q.question_id AS question_id, q.text AS text, q.difficulty AS difficulty,
                   round(avg_score, 2) AS avg_score, answers
            ORDER BY avg_score ASC LIMIT 10"""),
    }


# ------------------------------------------------------------------ GDS (with fallbacks)
def _with_projection(name: str, nodes: list[str], rels: dict, algo: str) -> list[dict]:
    try:
        run("CALL gds.graph.drop($name, false)", name=name)
        run("CALL gds.graph.project($name, $nodes, $rels)", name=name, nodes=nodes, rels=rels)
        return run(algo, name=name)
    finally:
        try:
            run("CALL gds.graph.drop($name, false)", name=name)
        except Exception:
            pass


def _pagerank() -> dict:
    try:
        items = _with_projection(
            "ikgRank", ["Skill", "Question", "Candidate"],
            {"TESTS_SKILL": {"orientation": "NATURAL"}, "HAS_SKILL": {"orientation": "NATURAL"}},
            """CALL gds.pageRank.stream($name) YIELD nodeId, score
               WITH gds.util.asNode(nodeId) AS n, score WHERE n:Skill
               RETURN n.name AS name, round(score, 4) AS score ORDER BY score DESC LIMIT 10""")
        return {"engine": "gds", "algorithm": "PageRank", "items": items}
    except Exception as exc:
        items = run("""MATCH (s:Skill) OPTIONAL MATCH (s)<-[r:TESTS_SKILL|HAS_SKILL]-()
                       RETURN s.name AS name, count(r) AS score ORDER BY score DESC LIMIT 10""")
        return {"engine": "fallback", "algorithm": "Degree centrality", "note": f"GDS unavailable: {str(exc)[:120]}", "items": items}


def _louvain() -> dict:
    try:
        items = _with_projection(
            "ikgCommunity", ["Skill", "Question"], {"TESTS_SKILL": {"orientation": "UNDIRECTED"}},
            """CALL gds.louvain.stream($name) YIELD nodeId, communityId
               WITH gds.util.asNode(nodeId) AS n, communityId WHERE n:Skill
               RETURN communityId AS community, collect(n.name) AS skills ORDER BY size(skills) DESC""")
        return {"engine": "gds", "algorithm": "Louvain", "items": items}
    except Exception as exc:
        items = run("MATCH (s:Skill) RETURN s.category AS community, collect(s.name) AS skills ORDER BY size(skills) DESC")
        return {"engine": "fallback", "algorithm": "Grouping by skill category", "note": f"GDS unavailable: {str(exc)[:120]}", "items": items}


def _similarity() -> dict:
    try:
        items = _with_projection(
            "ikgSim", ["Candidate", "Skill"], {"HAS_SKILL": {"orientation": "NATURAL"}},
            """CALL gds.nodeSimilarity.stream($name) YIELD node1, node2, similarity
               WITH gds.util.asNode(node1) AS a, gds.util.asNode(node2) AS b, similarity
               WHERE a.candidate_id < b.candidate_id
               RETURN a.candidate_id AS a, b.candidate_id AS b, round(similarity, 3) AS similarity
               ORDER BY similarity DESC LIMIT 10""")
        return {"engine": "gds", "algorithm": "Node Similarity", "items": items}
    except Exception as exc:
        smap = candidate_skill_map()
        ids, pairs = sorted(smap), []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                shared, pct = jaccard(smap[a]["skills"], smap[b]["skills"])
                if shared:
                    pairs.append({"a": a, "b": b, "similarity": round(pct / 100, 3)})
        pairs.sort(key=lambda x: -x["similarity"])
        return {"engine": "fallback", "algorithm": "Jaccard (Python)", "note": f"GDS unavailable: {str(exc)[:120]}", "items": pairs[:10]}


def gds_analytics() -> dict:
    return {"pagerank": _pagerank(), "louvain": _louvain(), "similarity": _similarity()}


# ------------------------------------------------------------------ MongoDB aggregations
def mongo_aggregations() -> dict:
    emo, iv = get_collection("emotion_logs"), get_collection("raw_interviews")
    avg_conf = list(emo.aggregate([{"$group": {"_id": None, "avg": {"$avg": "$confidence"}, "samples": {"$sum": 1}}},
                                   {"$project": {"_id": 0, "avg": {"$round": ["$avg", 3]}, "samples": 1}}]))
    return {
        "avg_emotion_confidence": avg_conf[0] if avg_conf else {"avg": None, "samples": 0},
        "emotion_distribution": list(emo.aggregate([
            {"$group": {"_id": "$label", "count": {"$sum": 1}, "avg_confidence": {"$avg": "$confidence"}}},
            {"$project": {"_id": 0, "label": "$_id", "count": 1, "avg_confidence": {"$round": ["$avg_confidence", 3]}}},
            {"$sort": {"count": -1}}])),
        "interviews_per_role": list(iv.aggregate([
            {"$group": {"_id": "$target_role", "interviews": {"$sum": 1}}},
            {"$project": {"_id": 0, "role": "$_id", "interviews": 1}}, {"$sort": {"interviews": -1}}])),
        "avg_answer_score": (list(iv.aggregate([
            {"$unwind": "$qa"}, {"$group": {"_id": None, "avg": {"$avg": "$qa.score"}, "answers": {"$sum": 1}}},
            {"$project": {"_id": 0, "avg": {"$round": ["$avg", 2]}, "answers": 1}}])) or [{"avg": None, "answers": 0}])[0],
        "candidate_stats": list(iv.aggregate([
            {"$unwind": "$qa"},
            {"$group": {"_id": "$candidate_id", "interviews": {"$addToSet": "$_id"}, "answers": {"$sum": 1},
                        "avg_score": {"$avg": "$qa.score"}}},
            {"$project": {"_id": 0, "candidate_id": "$_id", "interviews": {"$size": "$interviews"}, "answers": 1,
                          "avg_score": {"$round": ["$avg_score", 2]}}},
            {"$sort": {"avg_score": -1}}, {"$limit": 10}])),
        "emotion_trends": list(emo.aggregate([
            {"$group": {"_id": {"phase": "$phase", "label": "$label"}, "count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"}}},
            {"$project": {"_id": 0, "phase": "$_id.phase", "label": "$_id.label", "count": 1,
                          "avg_confidence": {"$round": ["$avg_confidence", 3]}}},
            {"$sort": {"phase": 1, "count": -1}}])),
    }


def catalog_skills() -> dict:
    return {"items": run("""
        MATCH (s:Skill)
        OPTIONAL MATCH (c:Candidate)-[:HAS_SKILL]->(s)
        WITH s, count(DISTINCT c) AS candidates
        OPTIONAL MATCH (q:Question)-[:TESTS_SKILL]->(s)
        RETURN s.skill_id AS skill_id, s.name AS name, s.category AS category, candidates, count(DISTINCT q) AS questions
        ORDER BY candidates DESC, name""" )}


def catalog_roles() -> dict:
    from app.services.shared import role_requirements
    stats = {r["title"]: r for r in roles_analytics()["roles"]}
    items = []
    for r in role_requirements():
        s = stats.get(r["title"], {})
        items.append({"role_id": r["role_id"], "title": r["title"], "department": r["department"],
                      "required_skills": r["required"], "questions": s.get("questions", 0),
                      "candidates": s.get("candidates", 0), "avg_score": s.get("avg_score")})
    return {"items": items}