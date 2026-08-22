import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    """Runtime settings kept intentionally small for the foundation phase."""

    app_name: str = "AI Risk Manager API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "sqlite:///./ai_risk_manager.db"
    agent_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-5"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./ai_risk_manager.db"),
        agent_provider=os.getenv("AGENT_PROVIDER", "mock"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5"),
    )
