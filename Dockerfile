# syntax=docker/dockerfile:1

# ---------- Stage 1: build the React SPA ----------
FROM node:20-slim AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: backend + bundled SPA ----------
FROM python:3.12-slim AS runtime

# uv for fast, reproducible dependency installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ENVIRONMENT=production \
    STORAGE_BACKEND=local

WORKDIR /app

# Install dependencies first (better layer caching)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application code
COPY backend/ ./
RUN uv sync --frozen --no-dev

# Bundle the built SPA so FastAPI can serve it at "/"
COPY --from=frontend /web/dist ./app/static

# Copy reference examples for OOD embedding calibration
COPY examples/ ./examples/

# Inference model (tracked via Git LFS at the repo root; resolved to real bytes
# by the host on checkout — HF Spaces / Render / CI all pull LFS before build).
COPY modelo_raiox_mendeley_ft.keras ./app/ml/artifacts/model.keras

EXPOSE 8000
# Render/Cloud Run/HF provide $PORT; default to 8000.
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
