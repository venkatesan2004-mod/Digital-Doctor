.PHONY: help build up up-dev down logs test migrate seed clean

help:
	@echo "Digital Doctor - Available Commands:"
	@echo "  make build      Build all container images"
	@echo "  make up         Start production containers"
	@echo "  make up-dev     Start development containers with live-reload"
	@echo "  make down       Stop and remove containers (preserves volumes)"
	@echo "  make logs       Tail container logs"
	@echo "  make test       Execute automated backend test suite"
	@echo "  make migrate    Run database migrations"
	@echo "  make seed       Seed synthetic demo clinical data"
	@echo "  make clean      Stop containers and remove volumes (DESTRUCTIVE)"

build:
	docker compose build

up:
	docker compose up -d

up-dev:
	docker compose -f compose.yaml -f compose.dev.yaml up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest -v

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m scripts.seed_data

clean:
	docker compose down -v
