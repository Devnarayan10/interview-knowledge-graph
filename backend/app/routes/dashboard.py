from fastapi import APIRouter

from app.services import analytics_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary():
    return analytics_service.dashboard_summary()
