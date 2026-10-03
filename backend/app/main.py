"""FastAPI application entry point."""

import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j.exceptions import ServiceUnavailable
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.database.mongodb import close_mongo_client, verify_mongodb_connection
from app.database.neo4j import close_neo4j_driver, verify_neo4j_connection
from app.database.schema import init_mongo_indexes, init_neo4j_schema
from app.routes import analytics, candidates, catalog, dashboard, evaluation, graph, interviews, questions
from app.routes import database as database_routes
from app.routes import recommendations, seed
from app.utils.errors import BadRequestError, ConflictError, NotFoundError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _wait_for_databases(retries: int = 30, delay: float = 2.0) -> tuple[bool, bool]:
    n = m = False
    for _ in range(retries):
        n, m = verify_neo4j_connection(), verify_mongodb_connection()
        if n and m:
            break
        time.sleep(delay)
    return n, m


def _auto_seed() -> None:
    from app.services import seed_service
    try:
        if seed_service.graph_is_empty():
            logger.info("Graph is empty - seeding from dataset")
            seed_service.seed_all()
        else:
            logger.info("Graph already populated - skipping auto-seed")
    except Exception as exc:
        logger.error("Auto-seed failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    neo4j_ok, mongo_ok = _wait_for_databases()
    logger.info("Neo4j connected: %s | MongoDB connected: %s", neo4j_ok, mongo_ok)
    if neo4j_ok:
        init_neo4j_schema()
    if mongo_ok:
        init_mongo_indexes()
    if settings.auto_seed and neo4j_ok and mongo_ok:
        threading.Thread(target=_auto_seed, daemon=True).start()
    yield
    close_neo4j_driver()
    close_mongo_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Interview Knowledge Graph API",
        description="Neo4j knowledge graph + MongoDB documents for synthetic interview analysis.",
        version="1.0.0", lifespan=lifespan, docs_url="/docs", redoc_url="/redoc",
    )
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(NotFoundError)
    async def _nf(_: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def _cf(_: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(BadRequestError)
    async def _br(_: Request, exc: BadRequestError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ServiceUnavailable)
    async def _neo(_: Request, exc: ServiceUnavailable):
        return JSONResponse(status_code=503, content={"detail": "Neo4j is unavailable"})

    @app.exception_handler(PyMongoError)
    async def _mongo(_: Request, exc: PyMongoError):
        return JSONResponse(status_code=503, content={"detail": "MongoDB is unavailable"})

    @app.get("/health")
    def health_check():
        return {"status": "ok", "neo4j": verify_neo4j_connection(), "mongodb": verify_mongodb_connection()}

    @app.get("/")
    def root():
        return {"message": "Interview Knowledge Graph API", "docs": "/docs", "health": "/health",
                "api_prefix": settings.api_prefix}

    for module in (dashboard, candidates, questions, interviews, evaluation, graph, analytics,
                   recommendations, database_routes, seed, catalog):
        app.include_router(module.router, prefix=settings.api_prefix)
    return app


app = create_app()