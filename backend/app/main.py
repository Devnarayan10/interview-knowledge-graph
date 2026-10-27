"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.mongodb import close_mongo_client, verify_mongodb_connection
from app.database.neo4j import close_neo4j_driver, verify_neo4j_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info("Starting Interview Knowledge Graph API")

    neo4j_ok = verify_neo4j_connection()
    mongo_ok = verify_mongodb_connection()
    logger.info("Neo4j connected: %s | MongoDB connected: %s", neo4j_ok, mongo_ok)

    if settings.auto_seed and neo4j_ok and mongo_ok:
        # Seeding will be implemented in Phase 4
        logger.info("Auto-seed enabled (seed module pending Phase 4)")

    yield

    close_neo4j_driver()
    close_mongo_client()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Interview Knowledge Graph API",
        description=(
            "AI-powered interview analysis system using Neo4j knowledge graph "
            "and MongoDB for raw interview data."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint for Docker and monitoring."""
        return {
            "status": "ok",
            "neo4j": verify_neo4j_connection(),
            "mongodb": verify_mongodb_connection(),
        }

    @app.get("/")
    async def root():
        """API root with navigation links."""
        return {
            "message": "Interview Knowledge Graph API",
            "docs": "/docs",
            "health": "/health",
            "api_prefix": settings.api_prefix,
        }

    # Route modules will be registered in Phase 5
    # from app.routes import candidates, questions, skills, analytics, interviews, graph
    # app.include_router(candidates.router, prefix=settings.api_prefix)
    # ...

    return app


app = create_app()
