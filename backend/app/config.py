from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "skill_genome"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True

    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    EMBEDDING_MODEL: str = "sbert"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
