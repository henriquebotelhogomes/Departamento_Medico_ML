"""Unit tests for the ML predictor — Grad-CAM, OOD detection, and inference.

When the model file is absent these tests are SKIPPED with an explicit reason.
Set REQUIRE_ML_TESTS=1 (e.g. in CI with the model available) to turn a missing
model into a hard FAILURE instead of a silent skip.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
REQUIRE_ML_TESTS = os.environ.get("REQUIRE_ML_TESTS") == "1"


def _model_unavailable(reason: str):
    if REQUIRE_ML_TESTS:
        pytest.fail(f"REQUIRE_ML_TESTS=1 but the ML model is unavailable: {reason}")
    pytest.skip(f"Model not available — skipping ML tests ({reason})")


@pytest.fixture(scope="module")
def predictor():
    """Load predictor once for all tests in this module."""
    from app.ml.predictor import get_predictor

    p = get_predictor()
    if not p.is_ready:
        try:
            p.load()
        except FileNotFoundError as exc:
            _model_unavailable(str(exc))
    return p


def _skip_if_model_missing(predictor):
    if not predictor.is_ready:
        _model_unavailable("predictor not ready")


def _predict(predictor, fixture_name: str) -> dict:
    """Run inference on a fixture image (predict expects raw bytes)."""
    return predictor.predict((FIXTURES / fixture_name).read_bytes())


class TestPredictorInference:
    """Test basic prediction functionality."""

    def test_predict_returns_valid_structure(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert "predicted_class" in result
        assert "confidence" in result
        assert "probs" in result
        assert "inference_ms" in result
        assert "is_ood" in result

    def test_confidence_range(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_predicted_class_in_range(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert result["predicted_class"] in [0, 1, 2, 3]

    def test_probs_sum_to_one(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "normal_sample.jpg")
        total = sum(result["probs"].values())
        assert abs(total - 1.0) < 0.01

    def test_probs_has_four_classes(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert len(result["probs"]) == 4

    def test_inference_time_reasonable(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        # Should be under 10 seconds even on CPU
        assert result["inference_ms"] < 10000


class TestGradCAM:
    """Test Grad-CAM explainability."""

    def test_gradcam_generated_for_xray(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert result["gradcam_image"] is not None

    def test_gradcam_is_base64_png(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert result["gradcam_image"].startswith("data:image/png;base64,")

    def test_gradcam_not_generated_for_ood(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "text_sample.png")
        if result["is_ood"]:
            assert result["gradcam_image"] is None


class TestOODDetection:
    """Test Out-of-Distribution detection."""

    def test_xray_is_in_distribution(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert result["is_ood"] is False

    def test_normal_xray_is_in_distribution(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "normal_sample.jpg")
        assert result["is_ood"] is False

    def test_text_image_is_ood(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "text_sample.png")
        assert result["is_ood"] is True

    def test_ood_has_similarity_score(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "text_sample.png")
        assert result["ood_similarity"] is not None
        assert 0.0 <= result["ood_similarity"] <= 1.0

    def test_ood_similarity_below_threshold(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "text_sample.png")
        if result["is_ood"]:
            assert result["ood_similarity"] < 0.45

    def test_xray_similarity_above_threshold(self, predictor):
        _skip_if_model_missing(predictor)
        result = _predict(predictor, "covid_sample.jpg")
        assert result["ood_similarity"] >= 0.45
