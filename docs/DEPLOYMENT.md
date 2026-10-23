# Digital Doctor: Docker & Production Deployment Guide

## 1. Prerequisites
- Host OS: Windows 10/11 with Docker Desktop, or Linux Server with Docker Engine & Compose v2.20+.
- Host Hardware: 4 CPU Cores, 8GB RAM minimum, 20GB free disk space.
- Network Ports: `5173` (Frontend), `8000` (Backend API), `3306` (MySQL), `8001` (ChromaDB).

---

## 2. Docker Compose Deployment Options

### 2.1 Development Mode (Live Hot Reloading)
```cmd
# Windows Batch
scripts\start-dev.bat

# Or direct Docker Compose command:
docker compose -f compose.yaml -f compose.dev.yaml up --build -d
```

### 2.2 Production Hardened Mode
```cmd
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

### 2.3 Container Status & Health Verification
```cmd
docker compose ps
```
All four services (`frontend`, `backend`, `mysql`, `chromadb`) must reach `healthy` status.

---

## 3. Database Migrations & Synthetic Data Seeding

### Execute Alembic Migrations:
```cmd
docker compose exec backend alembic upgrade head
```

### Seed Synthetic Demo Records:
```cmd
docker compose exec backend python -m app.scripts.seed_data
```

---

## 4. Teardown Procedure
```cmd
# Stop containers while preserving clinical MySQL & Chroma volumes:
docker compose down

# Note: Do not use 'docker compose down -v' in ordinary operations
# as it permanently destroys named volume data!
```
