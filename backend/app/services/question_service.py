"""Question bank CRUD."""

from app.schemas.question import QuestionCreate
from app.services.shared import run
from app.utils.errors import ConflictError, NotFoundError
from app.utils.helpers import new_id, skill_rows, slugify
from app.database.mongodb import get_collection

_WHERE = """
    ($q IS NULL OR toLower(q.text) CONTAINS toLower($q))
    AND ($category IS NULL OR q.category = $category)
    AND ($difficulty IS NULL OR q.difficulty = $difficulty)
    AND ($role IS NULL OR q.target_role = $role)
    AND ($experience IS NULL OR q.experience = $experience)
"""


def list_questions(q=None, category=None, difficulty=None, role=None, experience=None, page=1, page_size=20) -> dict:
    params = dict(q=q or None, category=category or None, difficulty=difficulty or None,
                  role=role or None, experience=experience or None)
    total = run(f"MATCH (q:Question) WHERE {_WHERE} RETURN count(q) AS n", **params)[0]["n"]
    items = run(f"""
        MATCH (q:Question) WHERE {_WHERE}
        OPTIONAL MATCH (q)-[:TESTS_SKILL]->(s:Skill)
        WITH q, collect(DISTINCT s.name) AS skills
        ORDER BY q.question_id
        SKIP $skip LIMIT $limit
        RETURN q.question_id AS question_id, q.text AS text, q.category AS category,
               q.difficulty AS difficulty, q.target_role AS target_role, q.experience AS experience, skills
    """, skip=(page - 1) * page_size, limit=page_size, **params)
    facets = run("""
        MATCH (q:Question)
        RETURN collect(DISTINCT q.category) AS categories, collect(DISTINCT q.difficulty) AS difficulties,
               collect(DISTINCT q.target_role) AS roles, collect(DISTINCT q.experience) AS experiences
    """)[0]
    facets = {k: sorted(x for x in v if x is not None) for k, v in facets.items()}
    return {"items": items, "total": total, "page": page, "page_size": page_size, "facets": facets}


def get_question(qid: str) -> dict:
    rows = run("""
        MATCH (q:Question {question_id:$id})
        OPTIONAL MATCH (q)-[:TESTS_SKILL]->(s:Skill)
        OPTIONAL MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q)
        RETURN q.question_id AS question_id, q.text AS text, q.category AS category, q.difficulty AS difficulty,
               q.target_role AS target_role, q.experience AS experience, q.keywords AS keywords,
               collect(DISTINCT s.name) AS skills, count(DISTINCT a) AS answers, round(avg(a.score), 2) AS avg_score
    """, id=qid)
    if not rows or rows[0]["question_id"] is None:
        raise NotFoundError(f"Question {qid} not found")
    return rows[0]


def _set_skills(qid: str, skills: list[str]) -> None:
    run("MATCH (:Question {question_id:$id})-[t:TESTS_SKILL]->() DELETE t", id=qid)
    rows = skill_rows(skills)
    if rows:
        run("""
            MATCH (q:Question {question_id:$id}) UNWIND $rows AS r
            MERGE (s:Skill {skill_id:r.id}) ON CREATE SET s.name=r.name, s.category=r.category
            MERGE (q)-[:TESTS_SKILL]->(s)
        """, id=qid, rows=rows)


def _set_role(qid: str, role: str | None) -> None:
    run("MATCH (:Question {question_id:$id})-[f:FOR_ROLE]->() DELETE f", id=qid)
    if role:
        run("""
            MATCH (q:Question {question_id:$id})
            MERGE (r:Role {role_id:$rid}) ON CREATE SET r.title=$role
            MERGE (q)-[:FOR_ROLE]->(r)
        """, id=qid, rid="R-" + slugify(role), role=role)


def create_question(p: QuestionCreate) -> dict:
    qid = p.question_id or new_id("Q")
    if run("MATCH (q:Question {question_id:$id}) RETURN q.question_id AS id", id=qid):
        raise ConflictError(f"Question {qid} already exists")
    run("""CREATE (q:Question {question_id:$id, text:$text, category:$category, difficulty:$difficulty,
                               target_role:$role, experience:$exp, keywords:$kw})""",
        id=qid, text=p.text, category=p.category, difficulty=p.difficulty, role=p.target_role,
        exp=p.experience, kw=p.keywords)
    _set_skills(qid, p.skills)
    _set_role(qid, p.target_role)
    return get_question(qid)


def update_question(qid: str, data: dict) -> dict:
    get_question(qid)
    skills = data.pop("skills", None)
    mapping = {"target_role": "target_role"}
    props = {mapping.get(k, k): v for k, v in data.items()}
    if props:
        run("MATCH (q:Question {question_id:$id}) SET q += $props", id=qid, props=props)
    if "target_role" in data:
        _set_role(qid, data["target_role"])
    if skills is not None:
        _set_skills(qid, skills)
    return get_question(qid)

def delete_question(qid: str) -> dict:
    get_question(qid)

    linked_answers = run("""
        MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q:Question {question_id:$id})
        RETURN count(DISTINCT a) AS total
    """, id=qid)[0]["total"]

    if linked_answers > 0:
        raise ConflictError(
            f"Cannot delete question {qid}: "
            f"{linked_answers} recorded answer(s) exist in Neo4j."
        )

    mongo_references = get_collection("raw_interviews").count_documents({
        "qa.question_id": qid
    })

    if mongo_references > 0:
        raise ConflictError(
            f"Cannot delete question {qid}: "
            f"{mongo_references} interview document(s) reference it in MongoDB."
        )

    run("""
        MATCH (q:Question {question_id:$id})
        DETACH DELETE q
    """, id=qid)

    return {"deleted": qid}