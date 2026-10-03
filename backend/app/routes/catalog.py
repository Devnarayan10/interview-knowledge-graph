from fastapi import APIRouter

from app.services import analytics_service

router = APIRouter(tags=["Catalog"])


@router.get("/skills")
def skills():
    return analytics_service.catalog_skills()


@router.get("/roles")
def roles():
    return analytics_service.catalog_roles()