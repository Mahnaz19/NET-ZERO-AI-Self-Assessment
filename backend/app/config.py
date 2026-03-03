from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./test.db"
    ENVIRONMENT: str = "development"

    # TODO: wire these into Azure OpenAI client configuration once LLM integration is implemented.
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

