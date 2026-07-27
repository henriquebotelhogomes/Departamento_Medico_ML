"""Unit tests for the ML predictor — Grad-CAM, OOD detection, and inference."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def predictor():
    """Load predictor once for all tests in this module."""
    from app.ml.predictor import get_predictor

    p = get_predictor()
    if not p.is_ready:
        p.load()
    return p


def _skip_if_model_missing(predictor):
    if not predictor.is_ready:
        pytest.skip("Model not available — skipping ML tests")


class TestPredictorInference:
    """Test basic prediction functionality."""

    def test_predict_returns_valid_structure(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert "predicted_class" in result
        assert "confidence" in result
        assert "probs" in result
        assert "inference_ms" in result
        assert "is_ood" in result

    def test_confidence_range(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_predicted_class_in_range(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert result["predicted_class"] in [0, 1, 2, 3]

    def test_probs_sum_to_one(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "normal_sample.jpg")
        total = sum(p["probability"] for p in result["probs"])
        assert abs(total - 1.0) < 0.01

    def test_probs_has_four_classes(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert len(result["probs"]) == 4

    def test_inference_time_reasonable(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        # Should be under 10 seconds even on CPU
        assert result["inference_ms"] < 10000


class TestGradCAM:
    """Test Grad-CAM explainability."""

    def test_gradcam_generated_for_xray(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert result["gradcam_image"] is not None

    def test_gradcam_is_base64_png(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert result["gradcam_image"].startswith("data:image/png;base64,")

    def test_gradcam_not_generated_for_ood(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "text_sample.png")
        if result["is_ood"]:
            assert result["gradcam_image"] is None


class TestOODDetection:
    """Test Out-of-Distribution detection."""

    def test_xray_is_in_distribution(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert result["is_ood"] is False

    def test_normal_xray_is_in_distribution(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "normal_sample.jpg")
        assert result["is_ood"] is False

    def test_text_image_is_ood(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "text_sample.png")
        assert result["is_ood"] is True

    def test_ood_has_similarity_score(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "text_sample.png")
        assert result["ood_similarity"] is not None
        assert 0.0 <= result["ood_similarity"] <= 1.0

    def test_ood_similarity_below_threshold(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "text_sample.png")
        if result["is_ood"]:
            assert result["ood_similarity"] < 0.45

    def test_xray_similarity_above_threshold(self, predictor):
        _skip_if_model_missing(predictor)
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert result["ood_similarity"] >= 0.45
