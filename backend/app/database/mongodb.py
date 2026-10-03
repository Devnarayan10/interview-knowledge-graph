"""MongoDB document database connection and collection access."""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        logger.info("MongoDB client initialized: %s", settings.mongodb_uri)
    return _client


def get_mongo_database() -> Database:
    return get_mongo_client()[get_settings().mongodb_database]


def get_collection(name: str) -> Collection:
    return get_mongo_database()[name]


def verify_mongodb_connection() -> bool:
    try:
        get_mongo_client().admin.command("ping")
        return True
    except Exception as exc:
        logger.error("MongoDB connection failed: %s", exc)
        return False


def close_mongo_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB client closed")