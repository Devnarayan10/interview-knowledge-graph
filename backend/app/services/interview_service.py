"""Interview sessions. Source of truth for flexible documents is MongoDB; graph is kept in sync."""

import logging
from datetime import datetime

from app.database.mongodb import get_collection
from app.schemas.interview import InterviewCreate, InterviewUpdate
from app.seed.loader import score_answer
from app.services.shared import run
from app.utils.errors import ConflictError, NotFoundError
from app.utils.helpers import new_id

logger = logging.getLogger(__name__)


def _col():
    return get_collection("raw_interviews")


def list_interviews(candidate_id=None, target_role=None, page=1, page_size=20) -> dict:
    flt = {}
    if candidate_id:
        flt["candidate_id"] = candidate_id
    if target_role:
        flt["target_role"] = target_role
    total = _col().count_documents(flt)
    items = list(_col().aggregate([
        {"$match": flt}, {"$sort": {"started_at": -1, "_id": 1}},
        {"$skip": (page - 1) * page_size}, {"$limit": page_size},
        {"$project": {"_id": 0, "interview_id": "$_id", "candidate_id": 1, "round_id": 1, "round_label": 1,
                      "round_number": 1, "target_role": 1, "started_at": 1, "status": 1,
                      "questions": {"$size": {"$ifNull": ["$qa", []]}},
                      "avg_score": {"$round": [{"$avg": "$qa.score"}, 2]}}},
    ]))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_interview(iid: str) -> dict:
    doc = _col().find_one({"_id": iid})
    if not doc:
        raise NotFoundError(f"Interview {iid} not found")
    doc["interview_id"] = doc.pop("_id")
    try:
        rows = run("""
            MATCH (a:Answer {candidate_id:$cid, round_id:$rid})
            OPTIONAL MATCH (a)-[:RECEIVED]->(f:Feedback)
            OPTIONAL MATCH (a)-[:DEMONSTRATES]->(s:Skill)
            RETURN a.answer_id AS answer_id, f.strengths AS strengths, f.weaknesses AS weaknesses,
                   f.summary AS summary, collect(DISTINCT s.name) AS skills
        """, cid=doc["candidate_id"], rid=iid)
        by_id = {r["answer_id"]: r for r in rows}
        for qa in doc.get("qa", []):
            g = by_id.get(qa.get("answer_id"))
            if g:
                qa["feedback"] = {"strengths": g["strengths"], "weaknesses": g["weaknesses"], "summary": g["summary"]}
                qa["skills_demonstrated"] = g["skills"]
    except Exception as exc:
        logger.warning("Graph enrichment skipped: %s", exc)
    return doc


def _sync_graph(doc: dict) -> None:
    run("""
        MATCH (c:Candidate {candidate_id:$cid})
        MERGE (r:InterviewRound {round_id:$rid})
        SET r.round_number=$num, r.round_label=$label, r.date=$date, r.candidate_id=$cid, r.target_role=$role
        MERGE (c)-[:PARTICIPATES_IN]->(r)
    """, cid=doc["candidate_id"], rid=doc["_id"], num=doc["round_number"], label=doc["round_label"],
        date=doc["started_at"].date().isoformat(), role=doc.get("target_role"))
    run("""
        UNWIND $qa AS x
        MATCH (c:Candidate {candidate_id:$cid}) MATCH (q:Question {question_id:x.question_id})
        MATCH (r:InterviewRound {round_id:$rid})
        MERGE (a:Answer {answer_id:x.answer_id})
        SET a.transcript_text=x.answer, a.score=x.score, a.timestamp=x.timestamp, a.candidate_id=$cid,
            a.round_id=$rid, a.question_id=x.question_id, a.word_count=size(split(x.answer, ' '))
        MERGE (c)-[:ANSWERED]->(a) MERGE (a)-[:IN_RESPONSE_TO]->(q) MERGE (r)-[:INCLUDES]->(q)
    """, cid=doc["candidate_id"], rid=doc["_id"], qa=doc["qa"])


def create_interview(p: InterviewCreate) -> dict:
    if not run("MATCH (c:Candidate {candidate_id:$id}) RETURN 1 AS ok", id=p.candidate_id):
        raise NotFoundError(f"Candidate {p.candidate_id} not found")
    n = _col().count_documents({"candidate_id": p.candidate_id})
    label = p.round_label or f"R{n + 1}"
    iid = f"{p.candidate_id}__{label}"
    if _col().find_one({"_id": iid}):
        raise ConflictError(f"Interview {iid} already exists")
    qrows = run("""MATCH (q:Question) WHERE q.question_id IN $ids
                   RETURN q.question_id AS id, q.text AS text, q.category AS category, q.difficulty AS difficulty,
                          q.keywords AS keywords, q.target_role AS role""",
                ids=[x.question_id for x in p.qa])
    qmap = {r["id"]: r for r in qrows}
    missing = [x.question_id for x in p.qa if x.question_id not in qmap]
    if missing:
        raise NotFoundError(f"Unknown question ids: {', '.join(missing)}")
    start = datetime.utcnow().replace(microsecond=0)
    qa, transcript = [], []
    for idx, item in enumerate(p.qa):
        q = qmap[item.question_id]
        score = item.score if item.score is not None else score_answer(item.answer_text, q["keywords"] or [], 0)[0]
        t = 120 + idx * 240
        qa.append({"question_id": q["id"], "question": q["text"], "category": q["category"],
                   "difficulty": q["difficulty"], "answer_id": new_id("A"), "answer": item.answer_text,
                   "score": score, "skills_tested": [], "keywords": q["keywords"] or [],
                   "timestamp": start.isoformat(), "timestamp_sec": t})
        transcript += [{"speaker": "interviewer", "text": q["text"], "t": t},
                       {"speaker": "candidate", "text": item.answer_text, "t": t + 30}]
    doc = {"_id": iid, "candidate_id": p.candidate_id, "round_id": iid, "round_label": label,
           "round_number": n + 1, "target_role": p.target_role or qrows[0]["role"], "started_at": start,
           "status": "completed", "transcript": transcript, "qa": qa, "emotion_timeline": [],
           "metadata": {"synthetic": False, "created_via": "api", "notes": p.notes or ""}}
    _col().insert_one(doc)
    _sync_graph(doc)
    return get_interview(iid)


def update_interview(iid: str, p: InterviewUpdate) -> dict:
    data = p.model_dump(exclude_unset=True)
    sets = {k: v for k, v in data.items() if k in ("target_role", "status")}
    if "notes" in data:
        sets["metadata.notes"] = data["notes"]
    sets["metadata.updated_at"] = datetime.utcnow().isoformat()
    res = _col().update_one({"_id": iid}, {"$set": sets})
    if res.matched_count == 0:
        raise NotFoundError(f"Interview {iid} not found")
    if "target_role" in data:
        run("MATCH (r:InterviewRound {round_id:$id}) SET r.target_role=$role", id=iid, role=data["target_role"])
    return get_interview(iid)


def delete_interview(iid: str) -> dict:
    doc = _col().find_one({"_id": iid}, {"candidate_id": 1})
    if not doc:
        raise NotFoundError(f"Interview {iid} not found")
    _col().delete_one({"_id": iid})
    removed = get_collection("emotion_logs").delete_many({"interview_id": iid}).deleted_count
    run("MATCH (e:Emotion {candidate_id:$cid}) WHERE e.answer_id IN [(a:Answer {round_id:$rid}) | a.answer_id] DETACH DELETE e",
        cid=doc["candidate_id"], rid=iid)
    run("MATCH (a:Answer {round_id:$rid}) OPTIONAL MATCH (a)-[:RECEIVED]->(f:Feedback) DETACH DELETE f, a", rid=iid)
    run("MATCH (r:InterviewRound {round_id:$rid}) DETACH DELETE r", rid=iid)
    return {"deleted": iid, "emotion_logs_removed": removed}