"""
Skill Genome Platform — Configuration
======================================
Centralized settings loaded from environment variables.

WHY THIS APPROACH:
- pydantic-settings validates env vars at startup (fail fast, not at runtime)
- Type-safe: DB_PORT is always an int, not a string
- Single source of truth for all configuration
- .env file support for local development

ALTERNATIVE: os.getenv() scattered everywhere
WHY NOT: No validation, no type safety, hard to find all config values
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Database ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "skill_genome"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    # --- API ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True

    # --- MLflow ---
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    # --- Embedding ---
    EMBEDDING_MODEL: str = "word2vec"
    EMBEDDING_DIM: int = 100
    EMBEDDING_WINDOW: int = 5
    EMBEDDING_MIN_COUNT: int = 3

    # --- Clustering ---
    CLUSTER_METHOD: str = "kmeans"
    CLUSTER_N: int = 8

    @property
    def DATABASE_URL(self) -> str:
        """Construct MySQL connection string for SQLAlchemy."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.

    WHY lru_cache:
    - Settings are read once and reused across the app lifetime
    - Prevents re-reading .env file on every request
    - Standard FastAPI pattern for dependency injection
    """
    return Settings()
