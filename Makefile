.PHONY: install lint typecheck test e2e perf check dev up down

install:
	cd backend && pip install -e ".[dev]"

lint:
	cd backend && ruff check src tests

typecheck:
	cd backend && mypy src

test:
	cd backend && pytest

e2e:
	cd backend && pytest tests/e2e -m e2e -v

perf:
	cd backend && python scripts/perf_smoke.py

check: lint typecheck test

dev:
	cd backend && uvicorn jarvis.api.app:create_app --factory --reload

up:
	docker compose up --build

down:
	docker compose down
