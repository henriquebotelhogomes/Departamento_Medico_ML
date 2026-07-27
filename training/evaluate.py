"""
Evaluate a trained model and generate metrics/artifacts for the Model Card.

Usage:
    python evaluate.py --model ../models/chest_xray_model.keras --test-dir ../data/chest_xray/test
    python evaluate.py --model ../models/chest_xray_model.keras --test-dir ../data/chest_xray/test --output-dir ./results
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tensorflow as tf
from sklearn.metrics import (
    auc,
    classification_report,
    confusion_matrix,
    roc_curve,
)

CLASS_NAMES = ["Covid-19", "Normal", "Viral Pneumonia", "Bacterial Pneumonia"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate model and generate metrics")
    parser.add_argument("--model", required=True, help="Path to .keras model file")
    parser.add_argument("--test-dir", required=True, help="Path to test dataset directory")
    parser.add_argument("--output-dir", default="./evaluation_results", help="Output directory")
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    print(f"Loading model from {args.model}")
    model = tf.keras.models.load_model(args.model)

    print(f"Loading test data from {args.test_dir}")
    test_ds = tf.keras.utils.image_dataset_from_directory(
        args.test_dir,
        image_size=(256, 256),
        batch_size=32,
        label_mode="int",
        shuffle=False,
    )

    # Predictions
    y_true = np.concatenate([y.numpy() for _, y in test_ds])
    y_probs = model.predict(test_ds)
    y_pred = np.argmax(y_probs, axis=1)

    # --- Classification report ---
    report = classification_report(
        y_true, y_pred, target_names=CLASS_NAMES, output_dict=True
    )
    report_path = output / "classification_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nClassification report saved to {report_path}")

    # Print text report
    print("\n" + classification_report(y_true, y_pred, target_names=CLASS_NAMES))

    # --- Confusion Matrix ---
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
    )
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix — RadioAI Chest X-ray Classifier")
    plt.tight_layout()
    cm_path = output / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=150)
    plt.close()
    print(f"Confusion matrix saved to {cm_path}")

    # --- ROC Curves (one-vs-rest) ---
    plt.figure(figsize=(8, 6))
    auc_scores = {}
    for i, name in enumerate(CLASS_NAMES):
        y_bin = (y_true == i).astype(int)
        fpr, tpr, _ = roc_curve(y_bin, y_probs[:, i])
        roc_auc = auc(fpr, tpr)
        auc_scores[name] = roc_auc
        plt.plot(fpr, tpr, label=f"{name} (AUC={roc_auc:.3f})")

    plt.plot([0, 1], [0, 1], "k--", alpha=0.5)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves (One-vs-Rest) — RadioAI")
    plt.legend(loc="lower right")
    plt.tight_layout()
    roc_path = output / "roc_curves.png"
    plt.savefig(roc_path, dpi=150)
    plt.close()
    print(f"ROC curves saved to {roc_path}")

    # --- Summary JSON ---
    summary = {
        "accuracy": report["accuracy"],
        "f1_macro": report["macro avg"]["f1-score"],
        "f1_weighted": report["weighted avg"]["f1-score"],
        "per_class_auc": auc_scores,
        "per_class": {
            name: {
                "precision": report[name]["precision"],
                "recall": report[name]["recall"],
                "f1": report[name]["f1-score"],
                "support": report[name]["support"],
            }
            for name in CLASS_NAMES
        },
        "total_samples": int(len(y_true)),
    }
    summary_path = output / "evaluation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_path}")

    # --- Final output ---
    print(f"\n{'='*50}")
    print(f"  Accuracy:      {report['accuracy']:.4f}")
    print(f"  F1 (macro):    {report['macro avg']['f1-score']:.4f}")
    print(f"  F1 (weighted): {report['weighted avg']['f1-score']:.4f}")
    print(f"  Mean AUC:      {np.mean(list(auc_scores.values())):.4f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
