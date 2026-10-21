from fastapi import APIRouter
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.services import question_service

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.get("")
def list_questions(q: str | None = None, category: str | None = None, difficulty: str | None = None, role: str | None = None, experience: str | None = None, page: int = 1, page_size: int = 20):
    return question_service.list_questions(q, category, difficulty, role, experience, max(1, page), min(100, max(1, page_size)))

@router.get("/{question_id}")
def get_question(question_id: str):
    return question_service.get_question(question_id)

@router.post("")
def create_question(body: QuestionCreate):
    return question_service.create_question(body)

@router.put("/{question_id}")
def update_question(question_id: str, body: QuestionUpdate):
    return question_service.update_question(question_id, body.model_dump(exclude_unset=True))

@router.delete("/{question_id}")
def delete_question(question_id: str):
    return question_service.delete_question(question_id)
