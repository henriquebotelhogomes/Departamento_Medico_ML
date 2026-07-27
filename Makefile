# RadioAI — developer shortcuts
# Windows users: run these targets via `make` (Git Bash / WSL) or copy the commands.

.PHONY: help install dev-api dev-web test test-backend test-frontend lint build docs up down model seed

help:
	@echo "Targets:"
	@echo "  install        Install backend (uv) and frontend (npm) deps"
	@echo "  model          Copy the .keras model into backend/app/ml/artifacts"
	@echo "  dev-api        Run FastAPI with autoreload (http://localhost:8000)"
	@echo "  dev-web        Run the Vite dev server (http://localhost:5173)"
	@echo "  test           Run backend + frontend test suites"
	@echo "  lint           Ruff + ESLint"
	@echo "  build          Build the frontend production bundle"
	@echo "  docs           Serve MkDocs locally"
	@echo "  up / down      docker compose up / down"

install:
	cd backend && uv sync --extra dev
	cd frontend && npm install

model:
	cd backend && uv run python ../scripts/get_model.py

dev-api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev

seed:
	cd backend && uv run python ../scripts/seed_demo.py

test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest -q

test-frontend:
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check app scripts
	cd frontend && npm run lint

build:
	cd frontend && npm run build

docs:
	uv run --with mkdocs-material mkdocs serve

up:
	docker compose up --build

down:
	docker compose down
