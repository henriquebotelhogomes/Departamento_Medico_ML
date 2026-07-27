# RadioAI

A full-stack machine learning application for chest X-ray classification (4 classes) built with **FastAPI + React + TensorFlow/Keras**.

## Features

- **ML Inference**: ResNet50-based model achieves 92.5% accuracy (with TTA) on the Mendeley dataset.
- **Modern API**: FastAPI, async SQLAlchemy, JWT auth, structlog logging.
- **React SPA**: Drag & drop prediction, paginated history, recharts dashboard, dark mode.
- **Single container**: Production Docker image serves API + frontend from one process.
- **Config-driven**: SQLite locally / PostgreSQL (Supabase) in prod; local storage / Supabase Storage.

## Quick Start

```bash
make install    # install Python (uv) and JS deps
make model      # place the Keras model artifact
make dev-api    # run backend at :8000
make dev-web    # run frontend at :5173 (new terminal)
```

Log in with demo account: `demo123` / `demo123`.

## Tech Stack

| Layer     | Technology                                             |
|-----------|--------------------------------------------------------|
| ML        | TensorFlow-CPU 2.21 · Keras 3.15 · ResNet50           |
| Backend   | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic        |
| Frontend  | React 18 · Vite · TypeScript · Tailwind CSS · Recharts|
| Infra     | Docker (multi-stage) · Render · Supabase              |

## Documentation

Run `make docs` to browse the full docs locally or visit the hosted MkDocs site.
