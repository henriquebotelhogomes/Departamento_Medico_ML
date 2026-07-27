"""Prediction endpoints: inference, history listing, detail and deletion."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, func, select

from app.api.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.ml.labels import label_for
from app.ml.predictor import get_predictor
from app.models.prediction import Prediction
from app.schemas.prediction import (
    ClassProbability,
    PredictionListOut,
    PredictionOut,
    PredictionResult,
)
from app.storage import get_storage

router = APIRouter(prefix="/predictions", tags=["predictions"])
logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def _probs_to_list(probs: dict) -> list[ClassProbability]:
    items: list[ClassProbability] = []
    for key, value in probs.items():
        cid = int(key)
        items.append(ClassProbability(class_id=cid, label=label_for(cid), probability=float(value)))
    return sorted(items, key=lambda p: p.class_id)


@router.post("", response_model=PredictionResult, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    current_user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File(description="Chest X-ray image")],
) -> PredictionResult:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10 MB)",
        )

    predictor = get_predictor()
    try:
        result = predictor.predict(data)
    except Exception as exc:  # noqa: BLE001
        logger.error("inference_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not process image",
        ) from exc

    storage = get_storage()
    filename = file.filename or "upload"
    storage_key = await storage.save(data, filename=filename, content_type=file.content_type)

    record = Prediction(
        user_id=current_user.id,
        original_filename=filename,
        storage_key=storage_key,
        predicted_class=result["predicted_class"],
        label=result["label"],
        confidence=result["confidence"],
        probs={str(k): v for k, v in result["probs"].items()},
        inference_ms=result["inference_ms"],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "prediction_created",
        prediction_id=record.id,
        user_id=current_user.id,
        label=record.label,
        confidence=round(record.confidence, 4),
        inference_ms=record.inference_ms,
    )

    image_url = await storage.url(storage_key)
    return PredictionResult(
        id=record.id,
        predicted_class=record.predicted_class,
        label=record.label,
        confidence=record.confidence,
        probs=_probs_to_list(record.probs),
        inference_ms=record.inference_ms,
        image_url=image_url,
        gradcam_image=result.get("gradcam_image"),
        is_ood=result.get("is_ood", False),
        ood_similarity=result.get("ood_similarity"),
        created_at=record.created_at,
    )


@router.get("", response_model=PredictionListOut)
async def list_predictions(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    predicted_class: Annotated[int | None, Query(ge=0, le=3)] = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> PredictionListOut:
    conditions = [Prediction.user_id == current_user.id]
    if predicted_class is not None:
        conditions.append(Prediction.predicted_class == predicted_class)
    if date_from is not None:
        conditions.append(Prediction.created_at >= date_from)
    if date_to is not None:
        conditions.append(Prediction.created_at <= date_to)

    total = await db.scalar(select(func.count()).select_from(Prediction).where(*conditions))
    stmt = (
        select(Prediction)
        .where(*conditions)
        .order_by(Prediction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    storage = get_storage()
    items: list[PredictionOut] = []
    for row in rows:
        out = PredictionOut.model_validate(row)
        out.image_url = await storage.url(row.storage_key)
        items.append(out)

    return PredictionListOut(items=items, total=int(total or 0), page=page, page_size=page_size)


@router.get("/{prediction_id}", response_model=PredictionOut)
async def get_prediction(
    prediction_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> PredictionOut:
    record = await db.get(Prediction, prediction_id)
    if record is None or record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    out = PredictionOut.model_validate(record)
    out.image_url = await get_storage().url(record.storage_key)
    return out


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prediction(
    prediction_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    record = await db.get(Prediction, prediction_id)
    if record is None or record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    storage_key = record.storage_key
    await db.execute(delete(Prediction).where(Prediction.id == prediction_id))
    await db.commit()
    try:
        await get_storage().delete(storage_key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("storage_delete_failed", key=storage_key, error=str(exc))
