from fastapi import APIRouter
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.services import candidate_service

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("")
def list_candidates(q: str | None = None, domain: str | None = None, job_type: str | None = None, page: int = 1, page_size: int = 20):
    data = candidate_service.list_candidates(q=q, domain=domain, job_type=job_type)
    page, page_size = max(1, page), min(100, max(1, page_size))
    data["items"] = data["items"][(page-1)*page_size:page*page_size]
    data.update(page=page, page_size=page_size)
    return data

@router.get("/{candidate_id}")
def get_candidate(candidate_id: str):
    return candidate_service.get_candidate(candidate_id)

@router.post("")
def create_candidate(body: CandidateCreate):
    return candidate_service.create_candidate(body)

@router.put("/{candidate_id}")
def update_candidate(candidate_id: str, body: CandidateUpdate):
    return candidate_service.update_candidate(candidate_id, body.model_dump(exclude_unset=True))

@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: str):
    return candidate_service.delete_candidate(candidate_id)
