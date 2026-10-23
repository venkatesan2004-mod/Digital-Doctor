import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

database_url = settings.DATABASE_URL


def _create_engine_instance(url: str):
    if "sqlite" in url:
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    else:
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False,
            connect_args={"connect_timeout": 2} if "pymysql" in url else {},
        )


try:
    engine = _create_engine_instance(database_url)
    # Validate connection quickly
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Primary MySQL database connection established successfully.")
except Exception as e:
    logger.warning(
        f"Primary database ({database_url.split('@')[-1] if '@' in database_url else database_url}) unreachable ({str(e)[:60]}). "
        "Falling back to local SQLite store ('digital_doctor_dev.db') for standalone execution."
    )
    fallback_url = "sqlite:///digital_doctor_dev.db"
    engine = _create_engine_instance(fallback_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
