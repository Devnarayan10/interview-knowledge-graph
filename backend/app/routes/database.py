from fastapi import APIRouter

from app.services import database_service

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/neo4j")
def neo4j():
    return database_service.neo4j_info()


@router.get("/mongodb")
def mongodb():
    return database_service.mongodb_info()


@router.get("/indexes")
def indexes():
    return database_service.all_indexes()