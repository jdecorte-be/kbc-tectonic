import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "KBC Signal — Jev customer intelligence"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/tododb")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
