import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI PostgreSQL Todo API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/tododb")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
    JEV_API_URL: str = os.getenv("JEV_API_URL", "https://api.typesafe.ai/v1/systemone")
    JEV_API_KEY: str = os.getenv("JEV_API_KEY", "")
    JEV_MODEL: str = os.getenv("JEV_MODEL", "jev-latest")
    JEV_PRICE_PER_M_INPUT: float = float(os.getenv("JEV_PRICE_PER_M_INPUT", "0.042"))  # USD, output tokens are free
    JEV_TIMEOUT: float = float(os.getenv("JEV_TIMEOUT", "30"))

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
