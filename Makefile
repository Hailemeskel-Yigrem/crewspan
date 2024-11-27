.PHONY: up down migrate seed test lint install dev-api dev-web health

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
	ruff check apps packages
	cd apps/web && npm run lint

install:
	pip install -r apps/api/requirements.txt
	pip install -r apps/worker/requirements.txt
	pip install -e packages/common -e packages/sdk
	cd apps/web && npm ci

dev-api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

dev-web:
	cd apps/web && npm run dev

health:
	bash scripts/healthcheck.sh

generate:
	python -m tools.codegen.generate_api
	python -m tools.codegen.generate_web
	python -m tools.codegen.generate_tests
	python -m tools.codegen.generate_docs
	python -m tools.codegen.generate_infra
