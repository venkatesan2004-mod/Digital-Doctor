import time
import uuid
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.database import engine, Base, SessionLocal
from app.schemas.audit import HealthCheckResponse
from app.scripts.seed_data import seed_synthetic_data

# Import API v1 routers
from app.api.v1.auth import router as auth_router
from app.api.v1.front_office import router as front_office_router
from app.api.v1.kiosk import router as kiosk_router
from app.api.v1.consultations import router as consultations_router
from app.api.v1.clinical_records import router as clinical_records_router
from app.api.v1.documents import router as documents_router
from app.api.v1.clinician_review import router as clinician_review_router
from app.api.v1.audit import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing Digital Doctor service...")
    # Create tables automatically if using SQLite in standalone or test mode
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified.")
    except Exception as e:
        logger.warning(f"Database connection initialization notice: {str(e)}")

    # Seed synthetic demonstration records if enabled
    if settings.ENABLE_SYNTHETIC_SEED_DATA:
        try:
            db = SessionLocal()
            seed_synthetic_data(db)
            db.close()
            logger.info("Synthetic demonstration records verified.")
        except Exception as e:
            logger.warning(f"Seed data execution notice: {str(e)}")

    yield
    logger.info("Shutting down Digital Doctor service.")


app = FastAPI(
    title="Digital Doctor API",
    description="Hospital Self-Service AI Consultation Kiosk with Clinician Oversight",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to configured origins in hospital deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Assigns unique correlation ID and logs execution timing."""
    correlation_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        f"[{correlation_id}] {request.method} {request.url.path} "
        f"Status: {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Sanitized global exception handler preventing information leakage."""
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal hospital system error occurred. Please contact Technical Operations or the Front Desk.",
            "status": "ERROR"
        }
    )


# System Health Check Endpoint
@app.get("/health", response_model=HealthCheckResponse, tags=["System Health"])
def system_health():
    """Returns runtime health status for database, vector store, and AI provider."""
    # Check DB
    db_status = "healthy"
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable ({str(e)[:30]})"

    # Check Vector Store
    vector_status = "healthy (in-memory fallback active)"
    try:
        import httpx
        with httpx.Client(timeout=2.0) as client:
            res = client.get(f"{settings.CHROMA_URL}/api/v1/heartbeat")
            if res.status_code == 200:
                vector_status = "healthy (chromadb connected)"
    except Exception:
        pass

    return HealthCheckResponse(
        status="OPERATIONAL",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database=db_status,
        vector_store=vector_status,
        ai_provider=settings.AI_PROVIDER,
        timestamp=datetime.datetime.utcnow()
    )


# Mount Versioned API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(front_office_router, prefix="/api/v1")
app.include_router(kiosk_router, prefix="/api/v1")
app.include_router(consultations_router, prefix="/api/v1")
app.include_router(clinical_records_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(clinician_review_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
