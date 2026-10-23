# ==============================================================================
# DIGITAL DOCTOR BACKEND DOCKERFILE
# Multi-stage build for Development and Production
# ==============================================================================

# Base Python runtime
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development Target
FROM base AS development
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production Target
FROM base AS production

# Create non-root application user for container security
RUN groupadd -r ddgroup && useradd -r -g ddgroup -d /app -s /sbin/nologin dduser

COPY --chown=dduser:ddgroup . .

# Ensure upload directory exists and has appropriate permissions
RUN mkdir -p /app/uploads && chown -R dduser:ddgroup /app/uploads

USER dduser
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
