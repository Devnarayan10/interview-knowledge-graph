from fastapi import APIRouter

from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/candidate/{candidate_id}")
def roles(candidate_id: str):
    return recommendation_service.role_recommendations(candidate_id)


@router.get("/similar/{candidate_id}")
def similar(candidate_id: str):
    return recommendation_service.similar_candidates(candidate_id)


@router.get("/skill-gap/{candidate_id}")
def skill_gap(candidate_id: str, role_id: str):
    return recommendation_service.skill_gap(candidate_id, role_id)