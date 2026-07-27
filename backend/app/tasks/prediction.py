"""
Async prediction task — runs inference in a background Celery worker.

This decouples the heavy ML inference from the FastAPI request cycle,
allowing the API to return immediately with a task ID.
"""

from __future__ import annotations

from pathlib import Path

from app.worker import celery_app


@celery_app.task(bind=True, max_retries=2, time_limit=60)
def run_prediction_task(self, image_path: str, user_id: int) -> dict:
    """
    Execute model prediction in background.

    Args:
        image_path: Absolute path to the uploaded image file.
        user_id: ID of the user who requested the prediction.

    Returns:
        Prediction result dict (same structure as Predictor.predict()).
    """
    from app.ml.predictor import get_predictor

    predictor = get_predictor()
    if not predictor.is_ready:
        predictor.load()

    result = predictor.predict(Path(image_path))

    return {
        "user_id": user_id,
        "image_path": image_path,
        "predicted_class": result["predicted_class"],
        "label": result["label"],
        "confidence": result["confidence"],
        "probs": result["probs"],
        "is_ood": result.get("is_ood", False),
        "ood_similarity": result.get("ood_similarity"),
        "inference_ms": result["inference_ms"],
        # Note: gradcam_image excluded from task result (too large for Redis)
    }
