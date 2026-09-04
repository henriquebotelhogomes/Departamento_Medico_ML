# RadioAI — Backend

FastAPI service that loads the fine-tuned ResNet50 chest X-ray classifier, handles DICOM PS 3.15 de-identification, serves Multi-LLM clinical reporting (Gemini, GPT 5.6 Luna, DeepSeek V4, Qwen 3.7, Local Engine) and exposes authentication, inference, history, and statistics endpoints.

See the repository root `README.md` and `docs/` for full documentation.

## Quick start (local)

```bash
uv sync --extra dev
uv run python ../scripts/get_model.py      # copy the .keras model into app/ml/artifacts
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Running tests

```bash
uv run python -m pytest
```

API docs: http://localhost:8000/api/docs
