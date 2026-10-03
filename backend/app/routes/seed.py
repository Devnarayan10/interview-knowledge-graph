from fastapi import APIRouter, HTTPException

from app.services import seed_service

router = APIRouter(prefix="/seed", tags=["Seed"])


@router.post("")
def seed():
    try:
        return seed_service.seed_all()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))