"""Database introspection for the 'Database & NoSQL' page."""

from app.config import get_settings
from app.database.mongodb import get_mongo_database, verify_mongodb_connection
from app.database.neo4j import verify_neo4j_connection
from app.services.shared import run


def _neo4j_indexes() -> dict:
    return {
        "constraints": run("SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties RETURN name, type, labelsOrTypes, properties ORDER BY name"),
        "indexes": run("SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state RETURN name, type, labelsOrTypes, properties, state ORDER BY name"),
    }


def neo4j_info() -> dict:
    ok = verify_neo4j_connection()
    if not ok:
        return {"connected": False, "uri": get_settings().neo4j_uri}
    return {
        "connected": True, "uri": get_settings().neo4j_uri,
        "node_counts": run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC"),
        "relationship_counts": run("MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY count DESC"),
        **_neo4j_indexes(),
    }


def mongodb_info() -> dict:
    ok = verify_mongodb_connection()
    settings = get_settings()
    if not ok:
        return {"connected": False, "database": settings.mongodb_database}
    db = get_mongo_database()
    cols = []
    for name in sorted(db.list_collection_names()):
        sample = db[name].find_one({}, {"transcript": 0})
        if sample and isinstance(sample.get("qa"), list):
            sample["qa"] = sample["qa"][:1]
        if sample and isinstance(sample.get("emotion_timeline"), list):
            sample["emotion_timeline"] = sample["emotion_timeline"][:2]
        cols.append({"name": name, "documents": db[name].count_documents({}), "sample": sample})
    return {"connected": True, "database": settings.mongodb_database, "collections": cols}


def all_indexes() -> dict:
    out = {"neo4j": None, "mongodb": {}}
    try:
        out["neo4j"] = _neo4j_indexes()
    except Exception:
        out["neo4j"] = {"constraints": [], "indexes": [], "error": "Neo4j unavailable"}
    try:
        db = get_mongo_database()
        for name in sorted(db.list_collection_names()):
            out["mongodb"][name] = [{"name": k, "keys": [list(x) for x in v["key"]]} for k, v in db[name].index_information().items()]
    except Exception:
        out["mongodb"] = {"error": "MongoDB unavailable"}
    return out