# worker/pipeline.py
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime as ort
from PIL import Image
import io

logger = logging.getLogger("agristream.pipeline")

MODEL_PATH = Path("models/mobilenetv3.onnx")

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


@dataclass
class InferenceResult:
    class_id: int
    confidence: float
    image_mean_brightness: float
    top_k_classes: list[tuple[int, float]]  # (class_id, confidence) top 5
    confidence_heatmap: Optional[np.ndarray] = None  # 4×4 grid, None if explain=False


class InferencePipeline:
    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found at {model_path}")

        logger.info("Loading ONNX model from %s", model_path)
        self._session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )
        self._input_name = self._session.get_inputs()[0].name
        logger.info("Model loaded — input name: %s", self._input_name)

    def _preprocess(self, image_bytes: bytes) -> tuple[np.ndarray, float, Image.Image]:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((224, 224), Image.BILINEAR)

        arr = np.array(image, dtype=np.float32) / 255.0
        image_mean_brightness = float(np.mean(arr))
        arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
        arr = arr.transpose(2, 0, 1)
        arr = np.expand_dims(arr, axis=0)
        return arr, image_mean_brightness, image

    def _get_patch_confidence(
        self,
        image: Image.Image,
        target_class: int,
        patch_size: int = 112,
        stride: int = 56,
    ) -> np.ndarray:
        """Compute confidence heatmap via sliding window patches."""
        width, height = image.size
        heatmap_rows = (height - patch_size) // stride + 1
        heatmap_cols = (width - patch_size) // stride + 1
        heatmap = np.zeros((heatmap_rows, heatmap_cols), dtype=np.float32)

        for i in range(heatmap_rows):
            for j in range(heatmap_cols):
                y, x = i * stride, j * stride
                patch = image.crop((x, y, x + patch_size, y + patch_size))
                patch = patch.resize((224, 224), Image.BILINEAR)

                arr = np.array(patch, dtype=np.float32) / 255.0
                arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
                arr = arr.transpose(2, 0, 1)
                arr = np.expand_dims(arr, axis=0)

                outputs = self._session.run(None, {self._input_name: arr})
                logits = outputs[0][0]
                probs = np.exp(logits) / np.sum(np.exp(logits))
                heatmap[i, j] = probs[target_class]

        return heatmap

    def run(self, image_bytes: bytes, explain: bool = False) -> InferenceResult:
        input_tensor, image_mean_brightness, original_image = self._preprocess(image_bytes)

        outputs = self._session.run(None, {self._input_name: input_tensor})
        logits = outputs[0][0]

        probs = np.exp(logits) / np.sum(np.exp(logits))
        class_id = int(np.argmax(logits))
        confidence = float(probs[class_id])

        # Top-5 classes for transparency
        top_indices = np.argsort(probs)[-5:][::-1]
        top_k_classes = [(int(idx), float(probs[idx])) for idx in top_indices]

        # Optional: confidence heatmap (slow — 16 inferences for 4×4 grid)
        heatmap: Optional[np.ndarray] = None
        if explain:
            logger.info("Generating confidence heatmap (explain=True)")
            heatmap = self._get_patch_confidence(original_image, class_id)
            logger.info("Heatmap shape: %s", heatmap.shape)

        logger.info(
            "Inference complete",
            extra={
                "class_id": class_id,
                "confidence": round(confidence, 4),
                "explain": explain,
            },
        )
        return InferenceResult(
            class_id=class_id,
            confidence=confidence,
            image_mean_brightness=image_mean_brightness,
            top_k_classes=top_k_classes,
            confidence_heatmap=heatmap,
        )