"""Graph payloads for react-force-graph-2d, read live from Neo4j."""

from app.services.shared import run
from app.utils.errors import NotFoundError

DEFAULT_TYPES = ["Candidate", "Question", "Skill", "Role", "Company", "Answer", "Technology", "InterviewRound", "Emotion", "Feedback"]
_KEY = ("labels({v})[0] + ':' + toString(coalesce({v}.round_id, {v}.answer_id, {v}.question_id, "
        "{v}.skill_id, {v}.role_id, {v}.company_id, {v}.tech_id, {v}.emotion_id, "
        "{v}.feedback_id, {v}.candidate_id))")
_NAME = "coalesce({v}.name, {v}.title, {v}.answer_id, {v}.round_id, {v}.text)"


def _k(v: str) -> str:
    return _KEY.replace("{v}", v)


def _shorten(value, n=300):
    return value[:n] + "…" if isinstance(value, str) and len(value) > n else value


def _node(r: dict) -> dict:
    name = str(r["name"] or r["id"])
    return {"id": r["id"], "type": r["type"], "name": name if len(name) <= 60 else name[:57] + "…",
            "props": {k: _shorten(v) for k, v in (r["props"] or {}).items()}}


def _stats(nodes: list, links: list) -> dict:
    by_type: dict[str, int] = {}
    for n in nodes:
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    return {"nodes": len(nodes), "links": len(links), "by_type": by_type}


def _links_between(keys: list[str]) -> list[dict]:
    rows = run(f"""
        MATCH (a)-[r]->(b)
        WHERE {_k('a')} IN $keys AND {_k('b')} IN $keys
        RETURN {_k('a')} AS source, {_k('b')} AS target, type(r) AS type
    """, keys=keys)
    return rows


def full_graph(types: list[str] | None = None) -> dict:
    types = [t for t in (types or DEFAULT_TYPES) if t in DEFAULT_TYPES + ["Emotion", "Feedback"]]
    nodes = [_node(r) for r in run(f"""
        MATCH (n) WHERE labels(n)[0] IN $types
        RETURN labels(n)[0] AS type, {_k('n')} AS id, {_NAME.replace('{v}', 'n')} AS name, properties(n) AS props
    """, types=types)]
    links = run(f"""
        MATCH (a)-[r]->(b)
        WHERE labels(a)[0] IN $types AND labels(b)[0] IN $types
        RETURN {_k('a')} AS source, {_k('b')} AS target, type(r) AS type
    """, types=types)
    return {"nodes": nodes, "links": links, "stats": _stats(nodes, links)}


def candidate_graph(cid: str) -> dict:
    rows = run(f"""
        MATCH (c:Candidate {{candidate_id:$id}})
        CALL {{
            WITH c RETURN c AS n
            UNION WITH c MATCH (c)-[:ANSWERED]->(n:Answer) RETURN n
            UNION WITH c MATCH (c)-[:ANSWERED]->(:Answer)-[:IN_RESPONSE_TO]->(n:Question) RETURN n
            UNION WITH c MATCH (c)-[:PARTICIPATES_IN]->(n:InterviewRound) RETURN n
            UNION WITH c MATCH (c)-[:HAS_SKILL]->(n:Skill) RETURN n
            UNION WITH c MATCH (c)-[:INTERVIEWED_FOR]->(n:Role) RETURN n
            UNION WITH c MATCH (c)-[:HAS_SKILL]->(:Skill)-[:RELATED_TO]->(n:Technology) RETURN n
        }}
        RETURN DISTINCT labels(n)[0] AS type, {_k('n')} AS id, {_NAME.replace('{v}', 'n')} AS name, properties(n) AS props
    """, id=cid)
    if not rows:
        raise NotFoundError(f"Candidate {cid} not found")
    nodes = [_node(r) for r in rows]
    links = _links_between([n["id"] for n in nodes])
    return {"nodes": nodes, "links": links, "stats": _stats(nodes, links)}