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
