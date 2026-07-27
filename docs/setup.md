# Local Setup

## Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/)
- **Node.js 20+** and npm
- Git LFS (`git lfs install`)

## Install

```bash
# Clone and pull the model via LFS
git clone <repo> && cd Departamento_Medico_ML
git lfs pull

# Backend
cd backend
uv sync --extra dev           # install all deps
uv run python ../scripts/get_model.py  # place model artifact

# Frontend
cd ../frontend
npm install
```

## Run (development)

```bash
# Terminal 1 — API
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — SPA
cd frontend
npm run dev
```

Open <http://localhost:5173> and log in with **demo123 / demo123**.

The Vite dev server proxies `/api` requests to `:8000` so there are no CORS issues.

## Run with Docker Compose

```bash
docker compose up --build
```

Backend at `:8000`, frontend at `:5173`.

To simulate the production Postgres environment:

```bash
docker compose --profile postgres up --build
```

## Running tests

```bash
# Backend
cd backend && uv run pytest -q

# Frontend
cd frontend && npm run test
```

## Environment variables

Copy `.env.example` at the repo root to `.env` and fill in your secrets for production. See docs on Deploy for details.
