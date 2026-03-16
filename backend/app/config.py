from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./test.db"
    ENVIRONMENT: str = "development"

    # Background processing / Redis (optional in dev/CI)
    REDIS_URL: str | None = None  # e.g. redis://redis:6379/0

    # RAG provider: "auto", "parquet", or "pgvector"
    RAG_PROVIDER: str = "auto"

    # Azure OpenAI configuration
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_DEPLOYMENT: str | None = None

    # Pydantic v2 settings configuration.
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings loader so we only parse environment once.
    """
    return Settings()


settings = get_settings()

