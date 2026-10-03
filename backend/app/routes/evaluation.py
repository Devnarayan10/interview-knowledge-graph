from fastapi import APIRouter

from app.schemas.evaluation import EvaluationOut
from app.services import evaluation_service

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/{candidate_id}", response_model=EvaluationOut)
def evaluate(candidate_id: str):
    return evaluation_service.evaluate_candidate(candidate_id)