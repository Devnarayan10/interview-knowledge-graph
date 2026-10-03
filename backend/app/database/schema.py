"""Automatic Neo4j constraint/index and MongoDB index initialisation (idempotent)."""

import logging

from app.database.mongodb import get_collection
from app.database.neo4j import run_cypher

logger = logging.getLogger(__name__)

# (constraint name, label, property) - names match database/neo4j/constraints.cypher
NEO4J_CONSTRAINTS = [
    ("candidate_id_unique", "Candidate", "candidate_id"),
    ("question_id_unique", "Question", "question_id"),
    ("skill_id_unique", "Skill", "skill_id"),
    ("role_id_unique", "Role", "role_id"),
    ("company_id_unique", "Company", "company_id"),
    ("answer_id_unique", "Answer", "answer_id"),
    ("emotion_id_unique", "Emotion", "emotion_id"),
    ("feedback_id_unique", "Feedback", "feedback_id"),
    ("tech_id_unique", "Technology", "tech_id"),
    ("round_id_unique", "InterviewRound", "round_id"),
]

NEO4J_INDEXES = [
    ("candidate_name_idx", "Candidate", "name"),
    ("skill_name_idx", "Skill", "name"),
    ("question_category_idx", "Question", "category"),
    ("role_title_idx", "Role", "title"),
    ("company_name_idx", "Company", "name"),
    ("answer_candidate_idx", "Answer", "candidate_id"),
    ("answer_round_idx", "Answer", "round_id"),
]


def init_neo4j_schema() -> int:
    applied = 0
    for name, label, prop in NEO4J_CONSTRAINTS:
        try:
            run_cypher(f"CREATE CONSTRAINT {name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE")
            applied += 1
        except Exception as exc:
            logger.warning("Constraint %s skipped: %s", name, exc)
    for name, label, prop in NEO4J_INDEXES:
        try:
            run_cypher(f"CREATE INDEX {name} IF NOT EXISTS FOR (n:{label}) ON (n.{prop})")
            applied += 1
        except Exception as exc:
            logger.warning("Index %s skipped: %s", name, exc)
    return applied


def init_mongo_indexes() -> list[str]:
    created = []
    spec = {
        "raw_interviews": ["candidate_id", "round_id", "target_role", "started_at"],
        "emotion_logs": ["candidate_id", "interview_id", "label", "timestamp", "confidence"],
    }
    for coll, fields in spec.items():
        for field in fields:
            created.append(f"{coll}.{get_collection(coll).create_index([(field, 1)])}")
    return created