"""Prediction & statistics schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

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
    raw_image_data: str | None = None
    pure_heatmap: str | None = None
    dicom_metadata: dict[str, Any] | None = None
    is_ood: bool = False
    ood_similarity: float | None = None
    created_at: datetime


class ReportRequest(BaseModel):
    predicted_class: int
    label: str
    confidence: float
    probs: list[ClassProbability] | None = None
    model: str = "gemini-3.8-flash"
    dicom_metadata: dict[str, Any] | None = None
    override_label: str | None = None
    override_notes: str | None = None
    is_ambiguous: bool | None = None


class ReportResponse(BaseModel):
    model_used: str
    provider: str
    technique: str
    findings: str
    impression: str
    icd_10: str
    recommendations: str
    disclaimer: str
    generated_at: datetime


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
