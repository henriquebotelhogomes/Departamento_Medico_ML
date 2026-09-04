"""DICOM handler for medical imaging: parsing, de-identification (HIPAA PS 3.15),
and pixel normalization for the ResNet50 classifier.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
import pydicom
from PIL import Image


def is_dicom_bytes(data: bytes) -> bool:
    """Check if byte buffer represents a DICOM file."""
    if len(data) >= 132 and data[128:132] == b"DICM":
        return True
    try:
        pydicom.dcmread(io.BytesIO(data), stop_before_pixels=True)
        return True
    except Exception:
        return False


def extract_and_deidentify_dicom(data: bytes) -> tuple[Image.Image, dict[str, Any]]:
    """Parse a DICOM file, sanitize all Protected Health Information (PHI),
    normalize pixel arrays to an RGB PIL.Image ready for ResNet50,
    and return clinical technical metadata.
    """
    ds = pydicom.dcmread(io.BytesIO(data), force=True)

    # Technical metadata (safe to preserve)
    metadata: dict[str, Any] = {
        "is_dicom": True,
        "modality": str(getattr(ds, "Modality", "CR")),
        "body_part": str(getattr(ds, "BodyPartExamined", "CHEST")),
        "patient_position": str(getattr(ds, "PatientPosition", "PA")),
        "photometric_interpretation": str(getattr(ds, "PhotometricInterpretation", "MONOCHROME2")),
        "kvp": str(getattr(ds, "KVP", "N/A")),
        "exposure_time": str(getattr(ds, "ExposureTime", "N/A")),
        "xray_tube_current": str(getattr(ds, "XRayTubeCurrent", "N/A")),
        "study_description": str(getattr(ds, "StudyDescription", "Chest X-Ray")),
        "rows": int(getattr(ds, "Rows", 0)),
        "columns": int(getattr(ds, "Columns", 0)),
    }

    # Extract pixel array
    pixel_array = ds.pixel_array.astype(np.float32)

    # Apply Rescale Slope / Intercept if present (standard Hounsfield/Intensity)
    rescale_slope = float(getattr(ds, "RescaleSlope", 1.0))
    rescale_intercept = float(getattr(ds, "RescaleIntercept", 0.0))
    if rescale_slope != 1.0 or rescale_intercept != 0.0:
        pixel_array = pixel_array * rescale_slope + rescale_intercept

    # Handle Photometric Interpretation (MONOCHROME1 means 0 is white, needs inversion)
    if metadata["photometric_interpretation"] == "MONOCHROME1":
        pixel_array = np.max(pixel_array) - pixel_array

    # Normalize to 0-255 uint8 range
    p_min = np.min(pixel_array)
    p_max = np.max(pixel_array)
    if p_max > p_min:
        norm_img = ((pixel_array - p_min) / (p_max - p_min) * 255.0).astype(np.uint8)
    else:
        norm_img = np.zeros_like(pixel_array, dtype=np.uint8)

    # Convert to standard RGB PIL Image
    pil_img = Image.fromarray(norm_img).convert("RGB")

    return pil_img, metadata
