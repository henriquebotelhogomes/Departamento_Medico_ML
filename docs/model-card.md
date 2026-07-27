# Model Card — Chest X-ray Classifier

## Overview

| Field           | Value                             |
|-----------------|-----------------------------------|
| Architecture    | ResNet50 (ImageNet pre-trained)   |
| Input           | 256 × 256 × 3 RGB                |
| Classes         | 4 (see below)                     |
| Framework       | TensorFlow 2.21 / Keras 3.15     |
| Best accuracy   | **92.5%** (with TTA)              |

## Classes

| ID | Label                | Notes                                   |
|----|----------------------|-----------------------------------------|
| 0  | Covid-19             | Ground-glass opacities, bilateral       |
| 1  | Normal               | No pathological findings                |
| 2  | Viral pneumonia      | Interstitial / diffuse infiltrates      |
| 3  | Bacterial pneumonia  | Lobar / segmental consolidation         |

## Dataset

- **Source**: Mendeley Data (Chest X-ray dataset, combined + augmented).
- **Split**: ~80/10/10 (train / val / test), stratified by class.
- **Preprocessing**: Resize to 256×256, Keras `preprocess_input` (ImageNet normalization).

## Training procedure

1. Feature extraction: freeze all ResNet50 layers, train a new classifier head (~15 epochs).
2. Fine-tuning: unfreeze `conv5_block*` layers, train at reduced LR (~25 epochs).
3. Best weights selected by validation loss (EarlyStopping + ReduceLROnPlateau).

## Performance

| Metric            | Value  |
|-------------------|--------|
| Test accuracy     | ~90%   |
| TTA accuracy      | 92.5%  |
| Macro F1          | ~0.91  |

TTA (Test-Time Augmentation) flips the image horizontally and averages predictions.

## Limitations & ethical considerations

!!! warning "Not a clinical tool"
    This model is a **portfolio demonstration**. It is NOT validated for clinical use, has NOT undergone regulatory review (FDA/CE), and MUST NOT be used for medical diagnosis.

- Trained on a limited public dataset; may not generalize to different scanners, populations, or acquisition protocols.
- Class boundaries (especially viral vs. bacterial pneumonia) are simplified.
- Covid-19 detection from X-rays alone has well-documented limitations in clinical practice.
- Model confidence should not be interpreted as clinical certainty.
