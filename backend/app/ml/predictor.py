"""Model loading and inference with Grad-CAM explainability and OOD detection.

The trained Keras model already bakes ``preprocess_input`` (and the training-only
data-augmentation layers) into its graph, so at inference time we feed a raw RGB
image resized to 256x256 with pixel values in the [0, 255] range.

OOD (Out-of-Distribution) detection uses cosine similarity between the input
image embedding (GAP layer output) and the mean embedding computed from known
chest X-ray reference images. Images with low similarity are flagged.
"""

from __future__ import annotations

import base64
import io
import time
from pathlib import Path
from threading import Lock

import numpy as np
from PIL import Image

from app.core.logging import get_logger
from app.ml.dicom_handler import extract_and_deidentify_dicom, is_dicom_bytes
from app.ml.labels import NUM_CLASSES, OOD_CLASS_ID, label_for

logger = get_logger(__name__)

IMG_SIZE = (256, 256)

# Matplotlib-style "jet" colormap approximation for heatmap overlay (256 entries)
_JET_COLORS: np.ndarray | None = None


def _get_jet_colormap() -> np.ndarray:
    """Return a (256, 3) uint8 array approximating the jet colormap."""
    global _JET_COLORS
    if _JET_COLORS is not None:
        return _JET_COLORS
    x = np.linspace(0, 1, 256)
    r = np.clip(1.5 - np.abs(4 * x - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * x - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * x - 1), 0, 1)
    _JET_COLORS = (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)
    return _JET_COLORS


class Predictor:
    """Thread-safe lazy singleton around the Keras model."""

    def __init__(
        self,
        model_path: str | Path,
        enable_tta: bool = False,
        ood_threshold: float = 0.45,
        ood_reference_dir: str | Path | None = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.enable_tta = enable_tta
        self.ood_threshold = ood_threshold
        self.ood_reference_dir = Path(ood_reference_dir) if ood_reference_dir else None
        self._model = None
        self._conv_layer_idx: int | None = None
        self._gap_layer_idx: int | None = None
        self._head_layer_indices: list[int] = []
        self._ood_reference_mean: np.ndarray | None = None
        self._lock = Lock()

    # -- lifecycle ---------------------------------------------------------
    def load(self) -> None:
        """Load the model into memory (called once at startup)."""
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model file not found at {self.model_path}. "
                    "Run `python scripts/get_model.py` first."
                )
            import keras

            logger.info("model_loading", path=str(self.model_path))
            self._model = keras.models.load_model(self.model_path, compile=False)
            logger.info("model_loaded", inputs=str(self._model.input_shape))
            self._identify_gradcam_layers()
            self._compute_ood_reference()

    def _identify_gradcam_layers(self) -> None:
        """Identify the conv layer, GAP layer, and head layers for Grad-CAM + OOD.

        Model structure: input -> resnet50 (Functional) -> GAP -> cabeca (Sequential)
        We use the resnet50 output as the conv feature map.
        """
        layers = self._model.layers
        for i, layer in enumerate(layers):
            out_shape = getattr(layer.output, "shape", [])
            if len(out_shape) == 4 and i > 0:  # 4D conv output (skip input layer)
                self._conv_layer_idx = i
            elif (
                len(out_shape) == 2
                and self._conv_layer_idx is not None
                and self._gap_layer_idx is None
            ):
                # First 2D layer after conv = GAP
                self._gap_layer_idx = i
                self._head_layer_indices = list(range(i + 1, len(layers)))
        if self._conv_layer_idx is not None:
            logger.info(
                "gradcam_ready",
                conv_layer=layers[self._conv_layer_idx].name,
                gap_layer=layers[self._gap_layer_idx].name if self._gap_layer_idx else None,
                head_layers=[layers[j].name for j in self._head_layer_indices],
            )
        else:
            logger.warning("gradcam_no_conv_layer_found")

    def _compute_ood_reference(self) -> None:
        """Compute mean embedding from reference X-ray images for OOD detection."""
        if self._conv_layer_idx is None or self._gap_layer_idx is None:
            return
        if self.ood_reference_dir is None or not self.ood_reference_dir.exists():
            logger.warning("ood_reference_dir_missing", path=str(self.ood_reference_dir))
            return

        # Collect reference image files
        extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        ref_files = [f for f in self.ood_reference_dir.iterdir() if f.suffix.lower() in extensions]
        if not ref_files:
            logger.warning("ood_no_reference_images")
            return

        # Extract embeddings from reference images
        embeddings = []
        layers = self._model.layers
        conv_layer = layers[self._conv_layer_idx]
        gap_layer = layers[self._gap_layer_idx]
        for fpath in ref_files:
            try:
                img_bytes = fpath.read_bytes()
                batch, _, _ = self._preprocess(img_bytes)
                conv_out = conv_layer(batch)
                emb = gap_layer(conv_out).numpy()[0]  # (2048,)
                embeddings.append(emb)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ood_ref_image_failed", file=str(fpath), error=str(exc))

        if embeddings:
            self._ood_reference_mean = np.mean(embeddings, axis=0)
            # Normalize the mean vector for cosine similarity
            norm = np.linalg.norm(self._ood_reference_mean)
            if norm > 0:
                self._ood_reference_mean = self._ood_reference_mean / norm
            logger.info(
                "ood_reference_computed",
                n_images=len(embeddings),
                embedding_dim=self._ood_reference_mean.shape[0],
            )
        else:
            logger.warning("ood_no_valid_embeddings")

    def _cosine_similarity(self, embedding: np.ndarray) -> float:
        """Compute cosine similarity between an embedding and the reference mean."""
        if self._ood_reference_mean is None:
            return 1.0  # disable OOD if no reference
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return 0.0
        return float(np.dot(embedding / norm, self._ood_reference_mean))

    def _get_embedding(self, batch: np.ndarray) -> np.ndarray:
        """Extract the GAP embedding (2048-dim) for a preprocessed batch."""
        layers = self._model.layers
        conv_out = layers[self._conv_layer_idx](batch)
        emb = layers[self._gap_layer_idx](conv_out).numpy()[0]
        return emb

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    # -- inference ---------------------------------------------------------
    def _preprocess(self, image_bytes: bytes) -> tuple[np.ndarray, dict | None, str]:
        """Preprocess raw bytes (DICOM or standard image) to (1, 256, 256, 3) float32 batch,
        dicom_metadata (if applicable), and raw normalized image base64 data URI.
        """
        if is_dicom_bytes(image_bytes):
            pil_img, dicom_meta = extract_and_deidentify_dicom(image_bytes)
            resized = pil_img.resize(IMG_SIZE)
        else:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            resized = pil_img.resize(IMG_SIZE)
            dicom_meta = None

        arr = np.asarray(resized, dtype="float32")
        batch = np.expand_dims(arr, axis=0)

        # Base64 of preprocessed image for browser display (crucial for DICOM)
        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        raw_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

        return batch, dicom_meta, raw_b64

    def predict(self, image_bytes: bytes) -> dict:
        """Run inference: returns class, label, confidence, probs, OOD flag, DICOM meta,
        and latency.
        """
        if self._model is None:
            self.load()

        start = time.perf_counter()
        batch, dicom_meta, raw_b64 = self._preprocess(image_bytes)
        probs = self._model.predict(batch, verbose=0)[0]

        if self.enable_tta:
            flipped = batch[:, :, ::-1, :]  # horizontal flip
            probs_flip = self._model.predict(flipped, verbose=0)[0]
            probs = (probs + probs_flip) / 2.0

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        class_id = int(np.argmax(probs))

        # OOD detection via cosine similarity
        embedding = self._get_embedding(batch)
        similarity = self._cosine_similarity(embedding)
        is_ood = similarity < self.ood_threshold

        if is_ood:
            final_class_id = OOD_CLASS_ID
            final_label = label_for(OOD_CLASS_ID)
            final_confidence = 0.0
        else:
            final_class_id = class_id
            final_label = label_for(class_id)
            final_confidence = float(probs[class_id])

        # Generate Grad-CAM heatmap (only if in-distribution)
        gradcam_b64, pure_heatmap_b64 = (
            self._generate_gradcam(batch, class_id) if not is_ood else (None, None)
        )

        return {
            "predicted_class": final_class_id,
            "label": final_label,
            "confidence": final_confidence,
            "probs": {i: float(probs[i]) for i in range(NUM_CLASSES)},
            "inference_ms": round(elapsed_ms, 2),
            "gradcam_image": gradcam_b64,
            "raw_image_data": raw_b64,
            "pure_heatmap": pure_heatmap_b64,
            "dicom_metadata": dicom_meta,
            "is_ood": is_ood,
            "ood_similarity": round(similarity, 4),
        }

    def _generate_gradcam(self, batch: np.ndarray, class_id: int) -> tuple[str | None, str | None]:
        """Generate Grad-CAM heatmap overlaid on the input image, as well as a standalone
        transparent heatmap PNG for dynamic frontend opacity blending.
        """
        if self._conv_layer_idx is None:
            return None, None
        try:
            import tensorflow as tf

            layers = self._model.layers
            conv_layer = layers[self._conv_layer_idx]
            gap_layer = layers[self._gap_layer_idx]

            input_tensor = tf.constant(batch)
            with tf.GradientTape() as tape:
                # Forward through conv layer (resnet50)
                conv_output = conv_layer(input_tensor)
                tape.watch(conv_output)
                # Forward through remaining head layers (GAP + cabeca)
                x = conv_output
                x = gap_layer(x)
                for idx in self._head_layer_indices:
                    x = layers[idx](x)
                predictions = x
                class_score = predictions[:, class_id]

            # Gradients of the class score w.r.t. conv layer output
            grads = tape.gradient(class_score, conv_output)
            # Global average pooling of gradients → importance weights
            weights = tf.reduce_mean(grads, axis=(1, 2))  # (1, filters)
            # Weighted combination of feature maps
            cam = tf.reduce_sum(conv_output * weights[:, tf.newaxis, tf.newaxis, :], axis=-1)[
                0
            ]  # (H, W)
            # ReLU + normalize
            cam = tf.nn.relu(cam).numpy()
            if cam.max() > 0:
                cam = cam / cam.max()

            # Resize heatmap to original image size
            heatmap = Image.fromarray((cam * 255).astype(np.uint8)).resize(IMG_SIZE, Image.BILINEAR)
            heatmap_arr = np.asarray(heatmap)

            # Apply jet colormap
            jet = _get_jet_colormap()
            colored_heatmap = jet[heatmap_arr]  # (256, 256, 3)

            # Generate pure heatmap with alpha channel based on activation
            pure_rgba = np.zeros((IMG_SIZE[1], IMG_SIZE[0], 4), dtype=np.uint8)
            pure_rgba[:, :, :3] = colored_heatmap
            pure_rgba[:, :, 3] = heatmap_arr

            pure_buf = io.BytesIO()
            Image.fromarray(pure_rgba).save(pure_buf, format="PNG")
            pure_b64 = "data:image/png;base64," + base64.b64encode(pure_buf.getvalue()).decode(
                "utf-8"
            )

            # Standard overlay on original image (60% original + 40% heatmap)
            original = batch[0].astype(np.uint8)
            overlay = (0.6 * original + 0.4 * colored_heatmap).astype(np.uint8)

            img_out = Image.fromarray(overlay)
            buffer = io.BytesIO()
            img_out.save(buffer, format="PNG")
            overlay_b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode(
                "utf-8"
            )

            return overlay_b64, pure_b64
        except Exception as exc:  # noqa: BLE001
            logger.warning("gradcam_failed", error=str(exc))
            return None, None


_predictor: Predictor | None = None


def get_predictor() -> Predictor:
    """Return the process-wide predictor singleton."""
    global _predictor
    if _predictor is None:
        from app.core.config import settings

        _predictor = Predictor(
            model_path=settings.resolve_path(settings.model_path),
            enable_tta=settings.enable_tta,
            ood_threshold=settings.ood_threshold,
            ood_reference_dir=settings.resolve_path(settings.ood_reference_dir),
        )
    return _predictor
