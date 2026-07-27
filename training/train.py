"""
Treino reproduzível do modelo RadioAI.

Uso:
    python train.py --config config.yaml
    python train.py --config config.yaml --epochs 50 --lr 0.0001

Requer:
    - Dataset em data/chest_xray/ com estrutura ImageFolder (train/val/test × 4 classes)
    - GPU recomendada (NVIDIA com CUDA)
    - Dependências: pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import mlflow
import mlflow.tensorflow
import numpy as np
import tensorflow as tf
import yaml
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight

CLASS_NAMES = ["Covid-19", "Normal", "Viral Pneumonia", "Bacterial Pneumonia"]


def set_seeds(seed: int) -> None:
    """Set seeds for reproducibility."""
    np.random.seed(seed)
    tf.random.set_seed(seed)


def build_model(cfg: dict) -> tf.keras.Model:
    """Build ResNet50 + custom head model."""
    img_size = cfg["data"]["image_size"]

    base = tf.keras.applications.ResNet50(
        include_top=False,
        weights=cfg["model"]["weights"],
        input_shape=(img_size, img_size, 3),
        pooling="avg",
    )
    base.trainable = False  # freeze initially

    inputs = tf.keras.Input(shape=(img_size, img_size, 3))
    x = tf.keras.applications.resnet50.preprocess_input(inputs)
    x = base(x)
    x = tf.keras.layers.Dropout(cfg["model"]["dropout"])(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(cfg["model"]["dropout"])(x)
    outputs = tf.keras.layers.Dense(4, activation="softmax")(x)

    return tf.keras.Model(inputs, outputs, name="radioai_resnet50")


def load_dataset(path: Path, cfg: dict, shuffle: bool = True) -> tf.data.Dataset:
    """Load dataset from directory using keras utility."""
    return tf.keras.utils.image_dataset_from_directory(
        path,
        image_size=(cfg["data"]["image_size"], cfg["data"]["image_size"]),
        batch_size=cfg["data"]["batch_size"],
        seed=cfg["data"]["seed"],
        label_mode="int",
        shuffle=shuffle,
    )


def compute_weights(train_ds: tf.data.Dataset) -> dict[int, float]:
    """Compute balanced class weights from training data."""
    labels = np.concatenate([y.numpy() for _, y in train_ds])
    weights = compute_class_weight("balanced", classes=np.unique(labels), y=labels)
    return dict(enumerate(weights))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train RadioAI chest X-ray classifier")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    parser.add_argument("--epochs", type=int, help="Override total epochs")
    parser.add_argument("--lr", type=float, help="Override unfreeze learning rate")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    # CLI overrides
    if args.epochs:
        cfg["training"]["epochs"] = args.epochs
    if args.lr:
        cfg["model"]["unfreeze_lr"] = args.lr

    set_seeds(cfg["data"]["seed"])

    data_dir = Path(cfg["data"]["dataset_dir"])
    print(f"Loading data from {data_dir.resolve()}")

    # --- Data ---
    train_ds = load_dataset(data_dir / "train", cfg)
    val_ds = load_dataset(data_dir / "val", cfg, shuffle=False)
    test_ds = load_dataset(data_dir / "test", cfg, shuffle=False)

    class_weight_dict = compute_weights(train_ds)
    print(f"Class weights: {class_weight_dict}")

    # --- Model ---
    model = build_model(cfg)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(cfg["model"]["head_lr"]),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    # --- MLflow ---
    mlflow.set_tracking_uri(cfg["mlflow"]["tracking_uri"])
    mlflow.set_experiment(cfg["mlflow"]["experiment_name"])

    with mlflow.start_run():
        mlflow.log_params({
            "backbone": cfg["model"]["backbone"],
            "image_size": cfg["data"]["image_size"],
            "batch_size": cfg["data"]["batch_size"],
            "total_epochs": cfg["training"]["epochs"],
            "freeze_epochs": cfg["model"]["freeze_backbone_epochs"],
            "head_lr": cfg["model"]["head_lr"],
            "unfreeze_lr": cfg["model"]["unfreeze_lr"],
            "dropout": cfg["model"]["dropout"],
            "seed": cfg["data"]["seed"],
            "early_stopping_patience": cfg["training"]["early_stopping_patience"],
        })

        # Phase 1: Train head only (backbone frozen)
        print("\n=== Phase 1: Head only (backbone frozen) ===")
        model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=cfg["model"]["freeze_backbone_epochs"],
            class_weight=class_weight_dict,
        )

        # Phase 2: Unfreeze backbone and fine-tune with low LR
        print("\n=== Phase 2: Fine-tuning (backbone unfrozen) ===")
        model.layers[1].trainable = True  # ResNet50 layer
        model.compile(
            optimizer=tf.keras.optimizers.Adam(cfg["model"]["unfreeze_lr"]),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                patience=cfg["training"]["early_stopping_patience"],
                restore_best_weights=True,
                monitor="val_accuracy",
                mode="max",
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                factor=0.5, patience=3, monitor="val_loss"
            ),
        ]

        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=cfg["training"]["epochs"],
            class_weight=class_weight_dict,
            callbacks=callbacks,
        )

        # Log training metrics
        for epoch_idx, (acc, val_acc) in enumerate(
            zip(history.history["accuracy"], history.history["val_accuracy"])
        ):
            mlflow.log_metrics(
                {"train_accuracy": acc, "val_accuracy": val_acc},
                step=epoch_idx + cfg["model"]["freeze_backbone_epochs"],
            )

        # --- Evaluate on test set ---
        print("\n=== Evaluation on test set ===")
        y_true = np.concatenate([y.numpy() for _, y in test_ds])
        y_pred = np.argmax(model.predict(test_ds), axis=1)

        report = classification_report(
            y_true, y_pred, target_names=CLASS_NAMES, output_dict=True
        )
        cm = confusion_matrix(y_true, y_pred)

        mlflow.log_metrics({
            "test_accuracy": report["accuracy"],
            "test_f1_macro": report["macro avg"]["f1-score"],
            "test_f1_weighted": report["weighted avg"]["f1-score"],
            "test_precision_macro": report["macro avg"]["precision"],
            "test_recall_macro": report["macro avg"]["recall"],
        })

        # Per-class metrics
        for name in CLASS_NAMES:
            if name in report:
                mlflow.log_metrics({
                    f"{name}_precision": report[name]["precision"],
                    f"{name}_recall": report[name]["recall"],
                    f"{name}_f1": report[name]["f1-score"],
                })

        # Save model
        output_path = Path("../models/chest_xray_model.keras")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(output_path))
        mlflow.tensorflow.log_model(model, "model")
        mlflow.log_artifact(str(output_path))

        # Print results
        print(f"\nTest Accuracy: {report['accuracy']:.4f}")
        print(f"Test F1 (macro): {report['macro avg']['f1-score']:.4f}")
        print(f"Test F1 (weighted): {report['weighted avg']['f1-score']:.4f}")
        print(f"\nConfusion Matrix:\n{cm}")
        print(f"\nModel saved to {output_path.resolve()}")
        print(f"MLflow run: {mlflow.active_run().info.run_id}")


if __name__ == "__main__":
    main()
