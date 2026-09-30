from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "KBC Tectonic — Customer intelligence"
    DATABASE_URL: str = f"sqlite:///{ROOT / 'data' / 'bank.sqlite3'}"
    BANK_DATA_PATH: str = ""
    PRODUCTS_PATH: str = ""
    CATEGORY_DB_PATH: str = ""
    GENERATED_CLIENT_COUNT: int = Field(default=1000, ge=1, le=10000)
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
