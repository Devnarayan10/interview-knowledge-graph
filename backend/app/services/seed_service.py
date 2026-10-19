"""Idempotent seeding of Neo4j (MERGE) and MongoDB (upsert) from the synthetic CSV."""

import logging
from pathlib import Path

from pymongo import ReplaceOne

from app.database.mongodb import get_collection
from app.database.neo4j import run_cypher
from app.database.schema import init_mongo_indexes, init_neo4j_schema
from app.seed.loader import find_dataset, read_rows, transform

logger = logging.getLogger(__name__)

Q = {
    "skills": "UNWIND $rows AS r MERGE (s:Skill {skill_id:r.skill_id}) SET s.name=r.name, s.category=r.category",
    "roles": "UNWIND $rows AS r MERGE (x:Role {role_id:r.role_id}) SET x.title=r.title, x.department=r.department",
    "techs": "UNWIND $rows AS r MERGE (t:Technology {tech_id:r.tech_id}) SET t.name=r.name",
    "companies": """UNWIND $rows AS r
    MERGE (c:Company {company_id:r.company_id})
    SET c.name=r.name,
        c.industry=r.industry,
        c.synthetic=r.synthetic,
        c.data_source=r.data_source""",
    "candidates": """UNWIND $rows AS r MERGE (c:Candidate {candidate_id:r.candidate_id})
        SET c.name=r.name, c.email=r.email, c.experience_years=r.experience_years, c.education=r.education,
            c.domain=r.domain, c.job_type=r.job_type, c.skills=r.skills, c.source_id=r.source_id,
            c.experience_text=r.experience_text, c.synthetic=true""",
    "questions": """UNWIND $rows AS r MERGE (q:Question {question_id:r.question_id})
        SET q.text=r.text, q.difficulty=r.difficulty, q.category=r.category, q.target_role=r.target_role,
            q.experience=r.experience, q.keywords=r.keywords, q.synthetic=true
        WITH q, r MATCH (ro:Role {role_id:r.role_id}) MERGE (q)-[:FOR_ROLE]->(ro)""",
    "rounds": """UNWIND $rows AS r MATCH (c:Candidate {candidate_id:r.candidate_id})
        MERGE (rd:InterviewRound {round_id:r.round_id})
        SET rd.round_number=r.round_number, rd.round_label=r.round_label, rd.date=r.date,
            rd.candidate_id=r.candidate_id, rd.target_role=r.target_role
        MERGE (c)-[:PARTICIPATES_IN]->(rd)""",
    "candidate_roles": """UNWIND $rows AS r MATCH (c:Candidate {candidate_id:r.candidate_id})
        MATCH (ro:Role {role_id:r.role_id}) MERGE (c)-[:INTERVIEWED_FOR]->(ro)""",
    "answers": """UNWIND $rows AS r
        MATCH (c:Candidate {candidate_id:r.candidate_id}) MATCH (q:Question {question_id:r.question_id})
        MATCH (rd:InterviewRound {round_id:r.round_id})
        MERGE (a:Answer {answer_id:r.answer_id})
        SET a.transcript_text=r.transcript_text, a.score=r.score, a.keyword_coverage=r.keyword_coverage,
            a.word_count=r.word_count, a.timestamp=r.timestamp, a.candidate_id=r.candidate_id,
            a.round_id=r.round_id, a.question_id=r.question_id
        MERGE (c)-[:ANSWERED]->(a) MERGE (a)-[:IN_RESPONSE_TO]->(q) MERGE (rd)-[:INCLUDES]->(q)
        MERGE (f:Feedback {feedback_id:r.feedback_id})
        SET f.strengths=r.strengths, f.weaknesses=r.weaknesses, f.summary=r.summary
        MERGE (a)-[:RECEIVED]->(f)
        MERGE (e:Emotion {emotion_id:r.emotion_id})
        SET e.label=r.emotion_label, e.confidence=r.emotion_confidence, e.candidate_id=r.candidate_id,
            e.answer_id=r.answer_id
        MERGE (c)-[:EXPRESSED]->(e)""",
    "candidate_skills": "UNWIND $rows AS r MATCH (c:Candidate {candidate_id:r.candidate_id}) MATCH (s:Skill {skill_id:r.skill_id}) MERGE (c)-[:HAS_SKILL]->(s)",
    "question_skills": "UNWIND $rows AS r MATCH (q:Question {question_id:r.question_id}) MATCH (s:Skill {skill_id:r.skill_id}) MERGE (q)-[:TESTS_SKILL]->(s)",
    "answer_skills": "UNWIND $rows AS r MATCH (a:Answer {answer_id:r.answer_id}) MATCH (s:Skill {skill_id:r.skill_id}) MERGE (a)-[:DEMONSTRATES]->(s)",
    "role_skills": "UNWIND $rows AS r MATCH (s:Skill {skill_id:r.skill_id}) MATCH (x:Role {role_id:r.role_id}) MERGE (s)-[rel:REQUIRED_FOR]->(x) SET rel.weight=r.weight",
    "skill_tech": "UNWIND $rows AS r MATCH (s:Skill {skill_id:r.skill_id}) MATCH (t:Technology {tech_id:r.tech_id}) MERGE (s)-[:RELATED_TO]->(t)",
    "candidate_companies": "UNWIND $rows AS r MATCH (c:Candidate {candidate_id:r.candidate_id}) MATCH (co:Company {company_id:r.company_id}) MERGE (c)-[:APPLIED_TO]->(co)",
    "role_companies": "UNWIND $rows AS r MATCH (ro:Role {role_id:r.role_id}) MATCH (co:Company {company_id:r.company_id}) MERGE (ro)-[:OFFERED_BY]->(co)",
}

ORDER = [
    ("skills", "skills"),
    ("roles", "roles"),
    ("technologies", "techs"),
    ("companies", "companies"),
    ("candidates", "candidates"),
    ("questions", "questions"),
    ("rounds", "rounds"),
    ("candidate_roles", "candidate_roles"),
    ("answers", "answers"),
    ("candidate_skills", "candidate_skills"),
    ("question_skills", "question_skills"),
    ("answer_skills", "answer_skills"),
    ("role_skills", "role_skills"),
    ("skill_tech", "skill_tech"),
    ("candidate_companies", "candidate_companies"),
    ("role_companies", "role_companies"),
]


def _batches(rows: list, size: int = 500):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def load_neo4j(data: dict) -> None:
    for key, qname in ORDER:
        rows = data.get(key) or []
        for batch in _batches(rows):
            run_cypher(Q[qname], {"rows": batch})


def load_mongo(data: dict) -> None:
    iv, emo = get_collection("raw_interviews"), get_collection("emotion_logs")
    for coll, docs in ((iv, data["mongo_interviews"]), (emo, data["emotion_logs"])):
        for batch in _batches(docs, 500):
            coll.bulk_write(
                [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in batch],
                ordered=False
            )


def stats() -> dict:
    labels = {
        r["l"]: r["c"]
        for r in run_cypher("MATCH (n) RETURN labels(n)[0] AS l, count(*) AS c")
    }
    rels = run_cypher("MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]

    return {
        "candidates": labels.get("Candidate", 0),
        "questions": labels.get("Question", 0),
        "answers": labels.get("Answer", 0),
        "skills": labels.get("Skill", 0),
        "roles": labels.get("Role", 0),
        "companies": labels.get("Company", 0),
        "technologies": labels.get("Technology", 0),
        "rounds": labels.get("InterviewRound", 0),
        "relationships": rels,
        "mongo_interviews": get_collection("raw_interviews").count_documents({}),
        "emotion_logs": get_collection("emotion_logs").count_documents({}),
    }


def graph_is_empty() -> bool:
    return run_cypher(
        "MATCH (c:Candidate) RETURN count(c) AS n"
    )[0]["n"] == 0


def seed_all(path: str | None = None) -> dict:
    p = Path(path) if path else find_dataset()
    data = transform(read_rows(p))

    init_neo4j_schema()
    init_mongo_indexes()

    load_neo4j(data)
    load_mongo(data)

    logger.info("Seed complete from %s", p.name)

    return {
        "dataset": p.name,
        "report": data["report"],
        "stats": stats(),
        "note": "Synthetic dataset: candidate/question pairs are semantically matched, not real interviews.",
    }