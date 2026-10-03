from typing import Optional

from fastapi import APIRouter

from app.services import graph_service

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("")
def full_graph(types: Optional[str] = None):
    return graph_service.full_graph(types.split(",") if types else None)


@router.get("/candidate/{candidate_id}")
def candidate_graph(candidate_id: str):
    return graph_service.candidate_graph(candidate_id)