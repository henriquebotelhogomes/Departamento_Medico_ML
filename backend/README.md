# RadioAI — Backend

FastAPI service that loads the fine-tuned ResNet50 chest X-ray classifier and exposes
authentication, image inference, prediction history and statistics endpoints.

See the repository root `README.md` and `docs/` for full documentation.

## Quick start (local)

```bash
uv sync --extra dev
uv run python ../scripts/get_model.py      # copy the .keras model into app/ml/artifacts
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API docs: http://localhost:8000/api/docs
