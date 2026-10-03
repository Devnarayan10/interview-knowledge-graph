from fastapi import APIRouter, HTTPException
from app.database.neo4j import run_cypher
from app.schemas.api import CandidateCreate, CandidateUpdate

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("")
def list_candidates(
    q: str | None = None,
    domain: str | None = None,
    job_type: str | None = None,
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
        filters.append("""
            (
                toLower(c.name) CONTAINS toLower($q)
                OR toLower(c.candidate_id) CONTAINS toLower($q)
                OR toLower(c.education) CONTAINS toLower($q)
                OR any(skill IN coalesce(c.skills, []) WHERE toLower(skill) CONTAINS toLower($q))
            )
        """)
        params["q"] = q

    if domain:
        filters.append("c.domain = $domain")
        params["domain"] = domain

    if job_type:
        filters.append("c.job_type = $job_type")
        params["job_type"] = job_type

    where = "WHERE " + " AND ".join(filters) if filters else ""

    rows = run_cypher(f"""
        MATCH (c:Candidate)
        {where}
        RETURN c
        ORDER BY c.candidate_id
        SKIP $skip
        LIMIT $page_size
    """, params)

    count_rows = run_cypher(f"""
        MATCH (c:Candidate)
        {where}
        RETURN count(c) AS total
    """, params)

    facet_rows = run_cypher("""
        MATCH (c:Candidate)
        RETURN
            collect(DISTINCT c.domain) AS domains,
            collect(DISTINCT c.job_type) AS job_types
    """, {})

    items = [row["c"] for row in rows]
    total = count_rows[0]["total"] if count_rows else 0

    facets = facet_rows[0] if facet_rows else {
        "domains": [],
        "job_types": [],
    }

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "facets": {
            "domains": sorted([x for x in facets.get("domains", []) if x]),
            "job_types": sorted([x for x in facets.get("job_types", []) if x]),
        },
    }

@router.get("/{candidate_id}")
def get_candidate(candidate_id: str):
    rows = run_cypher("""
        MATCH (c:Candidate {candidate_id:$id})
        OPTIONAL MATCH (c)-[:ANSWERED]->(a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
        OPTIONAL MATCH (a)-[:DEMONSTRATES]->(s:Skill)
        RETURN c,
               collect(DISTINCT a) AS answers,
               collect(DISTINCT q) AS questions,
               collect(DISTINCT s) AS skills
    """, {"id": candidate_id})
    if not rows:
        raise HTTPException(404, "Candidate not found")
    return rows[0]

@router.post("")
def create_candidate(candidate: CandidateCreate):
    rows = run_cypher("""
        MERGE (c:Candidate {candidate_id:$candidate_id})
        SET c += $props
        RETURN c
    """, {"candidate_id": candidate.candidate_id, "props": candidate.model_dump(exclude={"candidate_id"})})
    return rows[0]

@router.put("/{candidate_id}")
def update_candidate(candidate_id: str, candidate: CandidateUpdate):
    props = {k:v for k,v in candidate.model_dump().items() if v is not None}
    if not props:
        raise HTTPException(400, "No fields supplied")
    rows = run_cypher("""
        MATCH (c:Candidate {candidate_id:$id})
        SET c += $props
        RETURN c
    """, {"id": candidate_id, "props": props})
    if not rows:
        raise HTTPException(404, "Candidate not found")
    return rows[0]

@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: str):
    rows = run_cypher("""
        MATCH (c:Candidate {candidate_id:$id})
        DETACH DELETE c
        RETURN $id AS deleted_candidate
    """, {"id": candidate_id})
    if not rows:
        raise HTTPException(404, "Candidate not found")
    return rows[0]
