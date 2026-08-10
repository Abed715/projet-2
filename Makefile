.PHONY: install lint typecheck test check dev up down

install:
	cd backend && pip install -e ".[dev]"

lint:
	cd backend && ruff check src tests

typecheck:
	cd backend && mypy src

test:
	cd backend && pytest

check: lint typecheck test

dev:
	cd backend && uvicorn jarvis.api.app:create_app --factory --reload

up:
	docker compose up --build

down:
	docker compose down
