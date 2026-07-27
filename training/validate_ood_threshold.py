"""
Validate the OOD (Out-of-Distribution) threshold with statistical analysis.

Uses two image sets:
  - in_distribution/: chest X-ray images (should have high cosine similarity)
  - out_distribution/: random non-X-ray images (should have low cosine similarity)

Outputs: ROC curve, similarity distribution histogram, optimal threshold.

Usage:
    python validate_ood_threshold.py \
        --model ../backend/app/ml/artifacts/model.keras \
        --reference-dir ../examples \
        --in-dist ../data/ood_validation/in_distribution \
        --out-dist ../data/ood_validation/out_distribution \
        --output-dir ./evaluation_results
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc, precision_recall_curve, roc_curve

# Add backend to path so we can import the predictor
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.ml.predictor import Predictor  # noqa: E402


def collect_similarities(predictor: Predictor, image_dir: Path) -> list[float]:
    """Compute cosine similarity for all images in a directory."""
    sims: list[float] = []
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    images = [p for p in image_dir.iterdir() if p.suffix.lower() in extensions]

    if not images:
        print(f"  WARNING: No images found in {image_dir}")
        return sims

    for img_path in images:
        try:
            embedding = predictor._get_embedding(img_path)
            sim = predictor._cosine_similarity(embedding, predictor._ood_reference_mean)
            sims.append(float(sim))
        except Exception as e:
            print(f"  SKIP {img_path.name}: {e}")

    return sims


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate OOD detection threshold")
    parser.add_argument("--model", default="../backend/app/ml/artifacts/model.keras")
    parser.add_argument("--reference-dir", default="../examples")
    parser.add_argument("--in-dist", default="../data/ood_validation/in_distribution")
    parser.add_argument("--out-dist", default="../data/ood_validation/out_distribution")
    parser.add_argument("--output-dir", default="./evaluation_results")
    parser.add_argument("--current-threshold", type=float, default=0.45)
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    print("Loading predictor...")
    predictor = Predictor(
        model_path=args.model,
        ood_threshold=args.current_threshold,
        ood_reference_dir=args.reference_dir,
    )
    predictor.load()

    print(f"Collecting in-distribution similarities from {args.in_dist}...")
    in_dist = collect_similarities(predictor, Path(args.in_dist))
    print(f"  Found {len(in_dist)} samples, mean={np.mean(in_dist):.4f}")

    print(f"Collecting out-of-distribution similarities from {args.out_dist}...")
    out_dist = collect_similarities(predictor, Path(args.out_dist))
    print(f"  Found {len(out_dist)} samples, mean={np.mean(out_dist):.4f}")

    if len(in_dist) < 5 or len(out_dist) < 5:
        print("\nERROR: Need at least 5 samples in each set for meaningful analysis.")
        print("Please add images to the in_distribution/ and out_distribution/ directories.")
        sys.exit(1)

    # Labels: 0 = in-distribution, 1 = out-of-distribution
    y_true = np.array([0] * len(in_dist) + [1] * len(out_dist))
    # Scores: 1 - similarity (higher score = more likely OOD)
    scores = np.array([1 - s for s in in_dist] + [1 - s for s in out_dist])

    # --- ROC Curve ---
    fpr, tpr, thresholds_roc = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)

    # Optimal threshold via Youden's J statistic
    j_scores = tpr - fpr
    optimal_idx = int(np.argmax(j_scores))
    optimal_score_threshold = thresholds_roc[optimal_idx]
    optimal_similarity_threshold = 1 - optimal_score_threshold

    # --- Precision-Recall ---
    precision, recall, _ = precision_recall_curve(y_true, scores)
    pr_auc = auc(recall, precision)

    # --- Print Results ---
    print(f"\n{'='*60}")
    print(f"  OOD Detection Validation Results")
    print(f"{'='*60}")
    print(f"  ROC AUC:                     {roc_auc:.4f}")
    print(f"  PR AUC:                      {pr_auc:.4f}")
    print(f"  Current threshold:           {args.current_threshold:.4f}")
    print(f"  Optimal threshold (Youden):  {optimal_similarity_threshold:.4f}")
    print(f"  In-dist similarity:          {np.mean(in_dist):.4f} ± {np.std(in_dist):.4f}")
    print(f"  Out-dist similarity:         {np.mean(out_dist):.4f} ± {np.std(out_dist):.4f}")
    print(f"  Separation gap:              {np.mean(in_dist) - np.mean(out_dist):.4f}")
    print(f"{'='*60}")

    # Performance at current threshold
    current_score = 1 - args.current_threshold
    tp = np.sum((scores >= current_score) & (y_true == 1))
    fp = np.sum((scores >= current_score) & (y_true == 0))
    fn = np.sum((scores < current_score) & (y_true == 1))
    tn = np.sum((scores < current_score) & (y_true == 0))

    tpr_at_current = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr_at_current = fp / (fp + tn) if (fp + tn) > 0 else 0

    print(f"\n  At current threshold ({args.current_threshold}):")
    print(f"    TPR (OOD detected):        {tpr_at_current:.4f} ({tp}/{tp+fn})")
    print(f"    FPR (X-rays rejected):     {fpr_at_current:.4f} ({fp}/{fp+tn})")
    print(f"{'='*60}\n")

    # --- Plots ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # ROC
    axes[0].plot(fpr, tpr, "b-", linewidth=2, label=f"ROC (AUC={roc_auc:.3f})")
    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5)
    axes[0].scatter(
        [fpr_at_current], [tpr_at_current],
        color="red", s=100, zorder=5,
        label=f"Current θ={args.current_threshold}",
    )
    axes[0].set_xlabel("False Positive Rate")
    axes[0].set_ylabel("True Positive Rate")
    axes[0].set_title("ROC Curve — OOD Detection")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Similarity Distribution
    axes[1].hist(in_dist, bins=25, alpha=0.7, label="In-distribution (X-rays)", color="green")
    axes[1].hist(out_dist, bins=25, alpha=0.7, label="Out-of-distribution", color="red")
    axes[1].axvline(
        args.current_threshold, color="blue", linestyle="--", linewidth=2,
        label=f"Current θ={args.current_threshold}",
    )
    axes[1].axvline(
        optimal_similarity_threshold, color="black", linestyle="-.", linewidth=2,
        label=f"Optimal θ={optimal_similarity_threshold:.3f}",
    )
    axes[1].set_xlabel("Cosine Similarity")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Similarity Distribution")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    # Precision-Recall
    axes[2].plot(recall, precision, "g-", linewidth=2, label=f"PR (AUC={pr_auc:.3f})")
    axes[2].set_xlabel("Recall")
    axes[2].set_ylabel("Precision")
    axes[2].set_title("Precision-Recall Curve — OOD")
    axes[2].legend()
    axes[2].grid(alpha=0.3)

    plt.tight_layout()
    plot_path = output / "ood_validation.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Plots saved to {plot_path}")

    # Save results as JSON
    import json

    results = {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "current_threshold": args.current_threshold,
        "optimal_threshold_youden": optimal_similarity_threshold,
        "in_distribution": {
            "n_samples": len(in_dist),
            "mean": float(np.mean(in_dist)),
            "std": float(np.std(in_dist)),
            "min": float(np.min(in_dist)),
            "max": float(np.max(in_dist)),
        },
        "out_distribution": {
            "n_samples": len(out_dist),
            "mean": float(np.mean(out_dist)),
            "std": float(np.std(out_dist)),
            "min": float(np.min(out_dist)),
            "max": float(np.max(out_dist)),
        },
        "at_current_threshold": {
            "tpr": tpr_at_current,
            "fpr": fpr_at_current,
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
        },
    }
    results_path = output / "ood_validation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results JSON saved to {results_path}")


if __name__ == "__main__":
    main()
