from fastapi import APIRouter
from app.schemas.interview import InterviewCreate, InterviewUpdate
from app.services import interview_service

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.get("")
def list_interviews(candidate_id: str | None = None, target_role: str | None = None, page: int = 1, page_size: int = 15):
    return interview_service.list_interviews(candidate_id, target_role, max(1, page), min(100, max(1, page_size)))

@router.get("/{interview_id}")
def get_interview(interview_id: str):
    return interview_service.get_interview(interview_id)

@router.post("")
def create_interview(body: InterviewCreate):
    return interview_service.create_interview(body)

@router.put("/{interview_id}")
def update_interview(interview_id: str, body: InterviewUpdate):
    return interview_service.update_interview(interview_id, body)

@router.delete("/{interview_id}")
def delete_interview(interview_id: str):
    return interview_service.delete_interview(interview_id)
