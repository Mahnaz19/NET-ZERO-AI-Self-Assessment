from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str
    ENVIRONMENT: str = "development"

    # TODO: wire these into Azure OpenAI client configuration once LLM integration is implemented.
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_DEPLOYMENT: str | None = None

    class Config:
        # The project root .env lives two levels up from this file.
        # Use an absolute path so test runners started from the repo root can still find it.
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings loader so we only parse environment once.
    """
    return Settings()


settings = get_settings()

