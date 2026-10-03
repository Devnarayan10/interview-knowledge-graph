from fastapi import APIRouter, HTTPException
from app.database.neo4j import run_cypher
from app.schemas.api import QuestionCreate

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.get("")
def list_questions(
    q: str | None = None,
    category: str | None = None,
    difficulty: str | None = None,
    role: str | None = None,
    experience: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    skip = (page - 1) * page_size

    filters = []
    params = {
        "skip": skip,
        "page_size": page_size,
    }

    if q:
        filters.append("toLower(q.text) CONTAINS toLower($q)")
        params["q"] = q

    if category:
        filters.append("q.category = $category")
        params["category"] = category

    if difficulty:
        filters.append("q.difficulty = $difficulty")
        params["difficulty"] = difficulty

    if role:
        filters.append("""
            EXISTS {
                MATCH (q)-[:TESTS_SKILL]->(s:Skill)-[:REQUIRED_FOR]->(r:Role)
                WHERE r.role_id = $role OR r.name = $role
            }
        """)
        params["role"] = role

    if experience:
        filters.append("q.experience = $experience")
        params["experience"] = experience

    where = "WHERE " + " AND ".join(filters) if filters else ""

    rows = run_cypher(f"""
        MATCH (q:Question)
        {where}
        RETURN q
        ORDER BY q.question_id
        SKIP $skip
        LIMIT $page_size
    """, params)

    count_rows = run_cypher(f"""
        MATCH (q:Question)
        {where}
        RETURN count(q) AS total
    """, params)

    items = [row["q"] for row in rows]
    total = count_rows[0]["total"] if count_rows else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@router.get("/{question_id}")
def get_question(question_id: str):
    rows = run_cypher("""
        MATCH (q:Question {question_id:$id})
        OPTIONAL MATCH (q)-[:TESTS_SKILL]->(s:Skill)
        OPTIONAL MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q)
        RETURN q,
               collect(DISTINCT s) AS skills,
               collect(DISTINCT a) AS answers
    """, {"id": question_id})

    if not rows:
        raise HTTPException(404, "Question not found")

    return rows[0]

@router.post("")
def create_question(q: QuestionCreate):
    rows = run_cypher("""
        MERGE (q:Question {question_id:$id})
        SET q.text=$text, q.difficulty=$difficulty, q.category=$category
        RETURN q
    """, {"id":q.question_id,"text":q.text,"difficulty":q.difficulty,"category":q.category})
    return rows[0]

@router.delete("/{question_id}")
def delete_question(question_id: str):
    rows = run_cypher("""
        MATCH (q:Question {question_id:$id}) DETACH DELETE q RETURN $id AS deleted_question
    """, {"id":question_id})
    if not rows: raise HTTPException(404, "Question not found")
    return rows[0]
