from typing import Optional

from fastapi import APIRouter

from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
def overview():
    return analytics_service.overview()


@router.get("/skills")
def skills(skill: Optional[str] = None):
    return analytics_service.skills_analytics(skill)


@router.get("/roles")
def roles():
    return analytics_service.roles_analytics()


@router.get("/difficulties")
def difficulties():
    return analytics_service.difficulties_analytics()


@router.get("/gds")
def gds():
    return analytics_service.gds_analytics()


@router.get("/mongo")
def mongo():
    return analytics_service.mongo_aggregations()