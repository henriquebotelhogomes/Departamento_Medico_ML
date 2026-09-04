# RadioAI

A full-stack machine learning application for chest X-ray classification (4 classes) built with **FastAPI + React + TensorFlow/Keras**.

## Features

- **ML Inference & Explainability**: ResNet50-based model achieves 92.5% accuracy (with TTA) on chest X-rays with Grad-CAM activation heatmaps.
- **Interactive PACS Workstation**: Real-time diagnostic viewer with Zoom, Brightness, Contrast, Inversion, and Grad-CAM opacity sliders.
- **DICOM Hospital Standard**: Native `.dcm` ingestion with PS 3.15 de-identification (HIPAA/LGPD) and technical metadata extraction.
- **Multi-LLM Radiology Reports**: Structured diagnostic reporting powered by Google Gemini 3.8 Flash, GPT 5.6 Luna, DeepSeek V4, Qwen 3.7, and Local Deterministic Engine with Side-by-Side Consensus.
- **Human-in-the-Loop (HITL)**: Ambiguity detection on tight-margin predictions and sovereign clinical override for attending physicians.
- **A4 Medical Print Engine**: Timbrated 1-page hospital report layout ready for PDF export with physician signature fields.
- **Modern API**: FastAPI, async SQLAlchemy, JWT auth, structlog logging.
- **Single Container**: Production Docker image serves API + frontend from one serverless Cloud Run or Render process.
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

| Layer     | Technology                                                                     |
|-----------|--------------------------------------------------------------------------------|
| ML / AI   | TensorFlow-CPU 2.21 · Keras 3.15 · ResNet50 · Grad-CAM · OOD Cosine Similarity |
| Imaging   | Pydicom · DICOM PS 3.15 De-identification · PACS Viewport                      |
| GenAI     | Google Gemini 3.8 Flash · GPT 5.6 Luna · DeepSeek V4 · Qwen 3.7 · Local Engine  |
| Backend   | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · SlowAPI                       |
| Frontend  | React 18 · Vite · TypeScript · Tailwind CSS · TanStack Query · i18next         |
| Infra     | Google Cloud Run (Scale-to-Zero $0/mo) · Docker (multi-stage) · Supabase       |

## Documentation

Run `make docs` to browse the full docs locally or visit the hosted MkDocs site.
