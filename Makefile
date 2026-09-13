.PHONY: up down migrate seed test lint typecheck coverage install dev-api dev-web health

up:
	docker compose up -d

down:
	docker compose down

migrate:
	cd apps/api && alembic upgrade head

seed:
	python scripts/seed.py

test:
	pytest apps/api/tests apps/worker/tests packages -v
	cd apps/web && npm test

lint:
	ruff check apps packages scripts
	cd apps/web && npm run lint

typecheck:
	cd apps/api && mypy app
	cd apps/web && npm run typecheck

coverage:
	cd apps/api && pytest tests --cov=app --cov-report=term-missing
	cd apps/web && npm run test:coverage

install:
	pip install -r apps/api/requirements.lock.txt
	pip install -r apps/worker/requirements.lock.txt
	pip install -e packages/common -e packages/sdk
	cd apps/web && npm ci

dev-api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

dev-web:
	cd apps/web && npm run dev

health:
	bash scripts/healthcheck.sh
