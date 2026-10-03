from fastapi import APIRouter, HTTPException
from app.database.mongodb import get_collection
from app.database.neo4j import run_cypher
from app.schemas.api import RawInterviewCreate

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.get("")
def list_interviews(
    candidate_id: str | None = None,
    target_role: str | None = None,
    page: int = 1,
    page_size: int = 15,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    skip = (page - 1) * page_size

    query = {}

    if candidate_id:
        query["candidate_id"] = candidate_id

    if target_role:
        query["target_role"] = target_role

    collection = get_collection("raw_interviews")

    total = collection.count_documents(query)

    items = list(
        collection.find(
            query,
            {"_id": 0}
        )
        .sort("round_id", 1)
        .skip(skip)
        .limit(page_size)
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@router.get("/{candidate_id}")
def candidate_interviews(candidate_id: str):
    return list(get_collection("raw_interviews").find({"candidate_id": candidate_id}, {"_id": 0}))

@router.post("")
def create_interview(interview: RawInterviewCreate):
    doc = interview.model_dump()
    result = get_collection("raw_interviews").insert_one(doc)
    return {"inserted_id": str(result.inserted_id), **doc}

@router.put("/{candidate_id}/{round_id}")
def update_interview(candidate_id: str, round_id: str, transcript: str):
    result = get_collection("raw_interviews").update_one(
        {"candidate_id": candidate_id, "round_id": round_id},
        {"$set": {"transcript": transcript}},
    )
    if not result.matched_count:
        raise HTTPException(404, "Interview not found")
    return {"matched": result.matched_count, "modified": result.modified_count}

@router.delete("/{candidate_id}/{round_id}")
def delete_interview(candidate_id: str, round_id: str):
    result = get_collection("raw_interviews").delete_many({"candidate_id": candidate_id, "round_id": round_id})
    return {"deleted": result.deleted_count}
