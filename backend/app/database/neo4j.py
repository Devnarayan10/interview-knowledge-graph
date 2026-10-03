"""Neo4j connection, schema application, and JSON-safe Cypher execution."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

from neo4j import Driver, GraphDatabase, Session

from app.config import get_settings

logger = logging.getLogger(__name__)
_driver: Optional[Driver] = None

CONSTRAINT_FILE_CANDIDATES = [
    Path("/app/database/neo4j/constraints.cypher"),
    Path(__file__).resolve().parents[3] / "database" / "neo4j" / "constraints.cypher",
    Path("database/neo4j/constraints.cypher"),
]


def get_neo4j_driver() -> Driver:
    global _driver
    if _driver is None:
        s = get_settings()
        _driver = GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
    return _driver


@contextmanager
def get_neo4j_session() -> Generator[Session, None, None]:
    s = get_settings()
    session = get_neo4j_driver().session(database=s.neo4j_database)
    try:
        yield session
    finally:
        session.close()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "labels") and hasattr(value, "items"):
        data = {k: _json_safe(v) for k, v in value.items()}
        data["_labels"] = list(value.labels)
        return data
    if hasattr(value, "type") and hasattr(value, "items"):
        return {"type": value.type, "properties": {k: _json_safe(v) for k, v in value.items()}}
    return value


def run_cypher(query: str, parameters: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    with get_neo4j_session() as session:
        result = session.run(query, parameters or {})
        return [_json_safe(record.data()) for record in result]


def verify_neo4j_connection() -> bool:
    try:
        with get_neo4j_session() as session:
            session.run("RETURN 1 AS ok").single()
        return True
    except Exception as exc:
        logger.error("Neo4j connection failed: %s", exc)
        return False


def close_neo4j_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _split_cypher_statements(text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        buffer.append(raw)
        if line.endswith(";"):
            stmt = "\n".join(buffer).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            buffer = []
    leftover = "\n".join(buffer).strip()
    if leftover:
        statements.append(leftover)
    return statements


def apply_neo4j_schema() -> dict[str, Any]:
    """Apply unique constraints and indexes from constraints.cypher."""
    path = next((p for p in CONSTRAINT_FILE_CANDIDATES if p.exists()), None)
    applied: list[str] = []
    errors: list[str] = []
    if path is None:
        logger.warning("constraints.cypher not found; using inline schema statements")
        statements = [
            "CREATE CONSTRAINT candidate_id_unique IF NOT EXISTS FOR (c:Candidate) REQUIRE c.candidate_id IS UNIQUE",
            "CREATE CONSTRAINT question_id_unique IF NOT EXISTS FOR (q:Question) REQUIRE q.question_id IS UNIQUE",
            "CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE",
            "CREATE CONSTRAINT role_id_unique IF NOT EXISTS FOR (r:Role) REQUIRE r.role_id IS UNIQUE",
            "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (co:Company) REQUIRE co.company_id IS UNIQUE",
            "CREATE CONSTRAINT answer_id_unique IF NOT EXISTS FOR (a:Answer) REQUIRE a.answer_id IS UNIQUE",
            "CREATE CONSTRAINT emotion_id_unique IF NOT EXISTS FOR (e:Emotion) REQUIRE e.emotion_id IS UNIQUE",
            "CREATE CONSTRAINT feedback_id_unique IF NOT EXISTS FOR (f:Feedback) REQUIRE f.feedback_id IS UNIQUE",
            "CREATE CONSTRAINT tech_id_unique IF NOT EXISTS FOR (t:Technology) REQUIRE t.tech_id IS UNIQUE",
            "CREATE CONSTRAINT round_id_unique IF NOT EXISTS FOR (ir:InterviewRound) REQUIRE ir.round_id IS UNIQUE",
            "CREATE INDEX candidate_name_idx IF NOT EXISTS FOR (c:Candidate) ON (c.name)",
            "CREATE INDEX skill_name_idx IF NOT EXISTS FOR (s:Skill) ON (s.name)",
            "CREATE INDEX question_category_idx IF NOT EXISTS FOR (q:Question) ON (q.category)",
            "CREATE INDEX role_title_idx IF NOT EXISTS FOR (r:Role) ON (r.title)",
            "CREATE INDEX company_name_idx IF NOT EXISTS FOR (co:Company) ON (co.name)",
            "CREATE INDEX candidate_domain_idx IF NOT EXISTS FOR (c:Candidate) ON (c.domain)",
            "CREATE INDEX question_difficulty_idx IF NOT EXISTS FOR (q:Question) ON (q.difficulty)",
            "CREATE INDEX answer_score_idx IF NOT EXISTS FOR (a:Answer) ON (a.score)",
            "CREATE INDEX skill_category_idx IF NOT EXISTS FOR (s:Skill) ON (s.category)",
        ]
    else:
        statements = _split_cypher_statements(path.read_text(encoding="utf-8"))
    for stmt in statements:
        try:
            run_cypher(stmt)
            applied.append(stmt.split("\n")[0][:120])
        except Exception as exc:
            logger.error("Schema statement failed: %s | %s", stmt, exc)
            errors.append(str(exc))
    return {"applied": len(applied), "errors": errors, "statements": applied}


def list_constraints() -> list[dict[str, Any]]:
    try:
        return run_cypher("SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties RETURN name, type, entityType, labelsOrTypes, properties")
    except Exception:
        return run_cypher("SHOW CONSTRAINTS")


def list_indexes() -> list[dict[str, Any]]:
    try:
        return run_cypher("SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state RETURN name, type, entityType, labelsOrTypes, properties, state")
    except Exception:
        return run_cypher("SHOW INDEXES")
