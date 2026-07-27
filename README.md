# RadioAI — Chest X-ray Classification

> Full-stack ML application: **FastAPI + React + TensorFlow/Keras** monorepo.

![Python](https://img.shields.io/badge/python-3.12-blue)
![TensorFlow](https://img.shields.io/badge/tensorflow--cpu-2.21-orange)
![React](https://img.shields.io/badge/react-18-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What is this?

A portfolio-ready application that classifies chest X-ray images into 4 classes using a fine-tuned ResNet50 model:

| Class | Label                |
|-------|----------------------|
| 0     | Covid-19             |
| 1     | Normal               |
| 2     | Viral pneumonia      |
| 3     | Bacterial pneumonia  |

**Accuracy**: 92.5% (with Test-Time Augmentation) on the Mendeley dataset.

> **Disclaimer**: This is a demonstration project — NOT a clinical tool.

---

## Features

- **Drag & drop prediction** with real-time probability bars and confidence badge.
- **Paginated history** with class filtering and detail modal (signed image URLs).
- **Dashboard** with bar/line charts (predictions by class, over time, average confidence).
- **JWT auth** (register/login/refresh) with a one-click demo account (`demo123 / demo123`).
- **Dark mode** with system preference detection.
- **Config-driven**: SQLite + local storage in dev; PostgreSQL + Supabase Storage in production.
- **Single-container deploy**: root `Dockerfile` bundles the React SPA inside the FastAPI image.
- **CI/CD**: GitHub Actions (lint, test, Docker build) + Render Blueprint.

---

## Quick Start

```bash
# Prerequisites: Python 3.12, uv, Node 20, Git LFS
git clone <repo> && cd Departamento_Medico_ML

# Backend
cd backend
uv sync --extra dev
uv run python ../scripts/get_model.py   # place the .keras model

# Frontend
cd ../frontend
npm install

# Run (two terminals)
cd backend  && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Open <http://localhost:5173> → log in with **demo123 / demo123**.

---

## Project Structure

```
backend/    FastAPI app, ML predictor, storage, DB, tests, Alembic
frontend/   React 18 + Vite + TypeScript + Tailwind + Recharts
docs/       MkDocs Material (architecture, model card, API, setup, deploy)
research/   Notebooks and training scripts (read-only reference)
scripts/    get_model.py, seed_demo.py
examples/   8 sample X-ray images for testing
```

---

## Tech Stack

| Layer     | Technologies                                                      |
|-----------|-------------------------------------------------------------------|
| ML        | TensorFlow-CPU 2.21 · Keras 3.15 · ResNet50 fine-tuned           |
| Backend   | Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 (async) · JWT |
| Frontend  | React 18 · Vite · TypeScript · Tailwind CSS · TanStack Query     |
| Data      | SQLite (dev) / PostgreSQL-Supabase (prod) · Supabase Storage     |
| DevOps    | Docker multi-stage · docker-compose · GitHub Actions · Render     |
| Tooling   | uv · ruff · Vitest · pytest · MkDocs Material                    |

---

## Documentation

```bash
# Serve locally
make docs
# or: uv run --with mkdocs-material mkdocs serve
```

---

## Testing

```bash
make test
# Backend: 17 tests (auth, predictions, stats, system)
# Frontend: 5 tests (components, login page)
```

---

## Deploy

See [docs/deploy.md](docs/deploy.md) for full instructions.

- **Render** (always-on): auto-detected via `render.yaml` Blueprint.
- **HuggingFace Spaces**: same Dockerfile, set `PORT=7860`.

---

## License

MIT
