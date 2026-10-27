"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Interview Knowledge Graph backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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

    # AI / NLP
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    llama_base_url: str = "http://localhost:11434"
    llama_model: str = "llama3"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    whisper_model: str = "base"
    ai_lazy_load: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str) -> str:
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
