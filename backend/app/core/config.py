from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_NAME: str = "Digital Doctor"

    FRONTEND_PORT: int = 5173
    BACKEND_PORT: int = 8000
    MYSQL_PORT: int = 3306
    CHROMA_PORT: int = 8001

    MYSQL_HOST: str = "mysql"
    MYSQL_DATABASE: str = "digital_doctor"
    MYSQL_USER: str = "digital_doctor_app"
    MYSQL_PASSWORD: str = "dev_secret_doctor_pw_2026"
    MYSQL_ROOT_PASSWORD: str = "dev_root_doctor_pw_2026"

    # Database URL: default connects to MySQL in docker, or SQLite for standalone tests
    DATABASE_URL: str = "mysql+pymysql://digital_doctor_app:dev_secret_doctor_pw_2026@mysql:3306/digital_doctor?charset=utf8mb4"

    # ChromaDB
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_URL: str = "http://chromadb:8000"
    CHROMA_COLLECTION_PREFIX: str = "dd_"

    # AI Configuration
    AI_PROVIDER: str = "mock"  # "mock" or "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TIMEOUT_SECONDS: int = 30

    EMBEDDING_PROVIDER: str = "mock"  # "mock" or "openai"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # HIMS Integration
    HIMS_PROVIDER: str = "mock"  # "mock" or "webhook"
    HIMS_API_URL: str = "http://mock-hims.internal/api/v1"
    HIMS_API_KEY: str = "synthetic_dev_hims_key"

    # Security & Tokens
    JWT_SECRET_KEY: str = "94c5e6f3a8b2d1c7e4f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    KIOSK_SESSION_TIMEOUT_MINUTES: int = 15
    KIOSK_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    KIOSK_RATE_LIMIT_WINDOW_SECONDS: int = 300

    # File Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: str = "pdf,png,jpg,jpeg"

    # Demo Mode
    DEMO_MODE: bool = True
    ENABLE_SYNTHETIC_SEED_DATA: bool = True
    DEMO_VERIFICATION_DEFAULT_YEAR: int = 1985

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")]


settings = Settings()
