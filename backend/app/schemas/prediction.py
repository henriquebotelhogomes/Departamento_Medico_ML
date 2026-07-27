"""Prediction & statistics schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClassProbability(BaseModel):
    class_id: int
    label: str
    probability: float


class PredictionResult(BaseModel):
    """Response returned right after an inference."""

    id: int
    predicted_class: int
    label: str
    confidence: float
    probs: list[ClassProbability]
    inference_ms: float
    image_url: str | None = None
    gradcam_image: str | None = None
    is_ood: bool = False
    ood_similarity: float | None = None
    created_at: datetime


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    predicted_class: int
    label: str
    confidence: float
    probs: dict
    inference_ms: float
    created_at: datetime
    image_url: str | None = None


class PredictionListOut(BaseModel):
    items: list[PredictionOut]
    total: int
    page: int
    page_size: int


class ClassCount(BaseModel):
    class_id: int
    label: str
    count: int


class TimePoint(BaseModel):
    date: str
    count: int


class StatsOut(BaseModel):
    total_predictions: int
    average_confidence: float
    by_class: list[ClassCount]
    over_time: list[TimePoint]
