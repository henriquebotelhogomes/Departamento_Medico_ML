"""Class labels for the 4-class chest X-ray classifier."""

from __future__ import annotations

# Index -> human-readable label (matches the training pipeline order).
CLASS_LABELS: dict[int, str] = {
    0: "Covid-19",
    1: "Normal",
    2: "Viral pneumonia",
    3: "Bacterial pneumonia",
}

NUM_CLASSES = len(CLASS_LABELS)

OOD_LABEL = "Out of Distribution"
OOD_CLASS_ID = -1


def label_for(class_id: int) -> str:
    if class_id == OOD_CLASS_ID:
        return OOD_LABEL
    return CLASS_LABELS.get(class_id, f"class_{class_id}")
