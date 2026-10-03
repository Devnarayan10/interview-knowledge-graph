"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "interview_graph_password"
    neo4j_database: str = "neo4j"

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "interview_db"

    # API
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Seeding
    auto_seed: bool = True
    dataset_path: str = ""  # optional explicit path to the CSV

    # Optional AI settings (not required; evaluation is deterministic)
    llm_provider: str = "mock"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()