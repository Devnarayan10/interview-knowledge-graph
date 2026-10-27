"""Neo4j graph database connection and session management."""

import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

from neo4j import Driver, GraphDatabase, Session

from app.config import get_settings

logger = logging.getLogger(__name__)

_driver: Optional[Driver] = None


def get_neo4j_driver() -> Driver:
    """Create or return the singleton Neo4j driver."""
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        logger.info("Neo4j driver initialized: %s", settings.neo4j_uri)
    return _driver


@contextmanager
def get_neo4j_session() -> Generator[Session, None, None]:
    """Provide a Neo4j session scoped to the configured database."""
    settings = get_settings()
    driver = get_neo4j_driver()
    session = driver.session(database=settings.neo4j_database)
    try:
        yield session
    finally:
        session.close()


def run_cypher(query: str, parameters: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Execute a Cypher query and return records as dictionaries."""
    with get_neo4j_session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


def verify_neo4j_connection() -> bool:
    """Verify Neo4j connectivity."""
    try:
        with get_neo4j_session() as session:
            session.run("RETURN 1 AS ok").single()
        return True
    except Exception as exc:
        logger.error("Neo4j connection failed: %s", exc)
        return False


def close_neo4j_driver() -> None:
    """Close the Neo4j driver on application shutdown."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")
