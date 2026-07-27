"""System endpoints: health check and version/metadata."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.ml.labels import CLASS_LABELS
from app.ml.predictor import get_predictor

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "model_loaded": get_predictor().is_ready}


@router.get("/version")
async def version() -> dict:
    return {
        "app": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "classes": CLASS_LABELS,
        "tta_enabled": settings.enable_tta,
    }
