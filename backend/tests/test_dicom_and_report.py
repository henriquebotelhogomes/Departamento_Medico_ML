"""Tests for DICOM processing and Multi-LLM report generation."""

from __future__ import annotations

from pathlib import Path
import httpx

from app.ml.dicom_handler import extract_and_deidentify_dicom, is_dicom_bytes
from tests.conftest import auth_headers


def test_dicom_handler_with_sample() -> None:
    sample_path = Path(__file__).resolve().parents[2] / "examples" / "dicom" / "sample_normal.dcm"
    assert sample_path.exists(), f"Sample DICOM not found at {sample_path}"

    data = sample_path.read_bytes()
    assert is_dicom_bytes(data) is True

    pil_img, meta = extract_and_deidentify_dicom(data)
    assert pil_img.size == (meta["columns"], meta["rows"])
    assert pil_img.mode == "RGB"
    assert meta["is_dicom"] is True
    assert meta["modality"] == "CR"
    assert meta["body_part"] == "CHEST"
    assert meta["patient_position"] == "PA"


async def test_predict_dicom_upload(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)
    sample_path = Path(__file__).resolve().parents[2] / "examples" / "dicom" / "sample_normal.dcm"
    data = sample_path.read_bytes()

    files = {"file": ("chest_exam.dcm", data, "application/dicom")}
    resp = await client.post("/api/predictions", files=files, headers=headers)
    assert resp.status_code == 201, resp.text

    body = resp.json()
    assert body["label"] == "Normal"
    assert body["predicted_class"] == 1


async def test_medical_report_endpoint(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)

    payload = {
        "predicted_class": 3,
        "label": "Pneumonia Bacteriana",
        "confidence": 0.942,
        "model": "deterministic-local",
        "dicom_metadata": {"patient_position": "PA", "kvp": "120"},
    }
    resp = await client.post("/api/predictions/report", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text

    report = resp.json()
    assert "J15.9" in report["icd_10"]
    assert "consolidação" in report["findings"].lower() or "alveolar" in report["findings"].lower()
    assert report["provider"] == "Local Rule-Based Medical Engine"


async def test_medical_report_clinical_override(client: httpx.AsyncClient) -> None:
    """Validate Human-in-the-Loop override alters the report according to physician judgment."""
    headers = await auth_headers(client)

    # Initial AI predicted Bacterial (51%), but Doctor intervened and overrode to Viral (49%)
    payload = {
        "predicted_class": 3,
        "label": "Pneumonia Bacteriana",
        "confidence": 0.51,
        "model": "deterministic-local",
        "override_label": "Pneumonia Viral",
        "override_notes": "Paciente com procalcitonina sérica normal (< 0.1 ug/L) e infiltrado intersticial difuso.",
        "is_ambiguous": True,
    }
    resp = await client.post("/api/predictions/report", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text

    report = resp.json()
    assert "J12.9" in report["icd_10"]  # Viral pneumonia ICD-10
    assert "SOBREESCRITA MÉDICA SOBERANA: Pneumonia Viral" in report["impression"]
    assert "procalcitonina" in report["impression"].lower()


async def test_llm_telemetry_and_finops_calculation(client: httpx.AsyncClient) -> None:
    """Validate token telemetry, FinOps cost calculation, and fallback telemetry."""
    from app.services.llm_report import calculate_llm_cost

    # 1. Direct mathematical cost validation
    gemini_cost = calculate_llm_cost("gemini-3.8-flash", 1000, 2000)
    expected_gemini = round((1000 * 0.075 / 1e6) + (2000 * 0.30 / 1e6), 6)
    assert gemini_cost == expected_gemini

    local_cost = calculate_llm_cost("deterministic-local", 500, 500)
    assert local_cost == 0.0

    # 2. Local deterministic report telemetry
    headers = await auth_headers(client)
    payload = {
        "predicted_class": 1,
        "label": "Normal",
        "confidence": 0.98,
        "model": "deterministic-local",
    }
    resp = await client.post("/api/predictions/report", json=payload, headers=headers)
    assert resp.status_code == 200
    report = resp.json()
    assert "telemetry" in report
    tel = report["telemetry"]
    assert tel is not None
    assert tel["prompt_tokens"] == 0
    assert tel["completion_tokens"] == 0
    assert tel["estimated_cost_usd"] == 0.0
    assert tel["fallback_triggered"] is False
    assert tel["latency_ms"] >= 0.0

    # 3. Gemini live telemetry (tokens and cost are extracted when key is configured)
    payload_gemini = {
        "predicted_class": 0,
        "label": "Covid-19",
        "confidence": 0.95,
        "model": "gemini-3.8-flash",
    }
    resp_gemini = await client.post("/api/predictions/report", json=payload_gemini, headers=headers)
    assert resp_gemini.status_code == 200
    report_gemini = resp_gemini.json()
    assert "telemetry" in report_gemini
    tel_gemini = report_gemini["telemetry"]
    assert tel_gemini is not None
    assert tel_gemini["latency_ms"] >= 0.0
    if not tel_gemini["fallback_triggered"]:
        assert tel_gemini["latency_ms"] > 0
        assert tel_gemini["prompt_tokens"] > 0
        assert tel_gemini["completion_tokens"] > 0
        assert tel_gemini["estimated_cost_usd"] > 0.0

    # 4. Explicit fallback telemetry validation
    from app.services.llm_report import _generate_deterministic_report
    from app.schemas.prediction import ReportRequest

    req = ReportRequest(predicted_class=2, label="Pneumonia Viral", confidence=0.88)
    fallback_rep = _generate_deterministic_report(
        req, fallback_reason="Simulated API Quota Limit 429", latency_ms=123.4
    )
    assert fallback_rep.telemetry is not None
    assert fallback_rep.telemetry.fallback_triggered is True
    assert fallback_rep.telemetry.fallback_reason == "Simulated API Quota Limit 429"
    assert fallback_rep.telemetry.latency_ms == 123.4
