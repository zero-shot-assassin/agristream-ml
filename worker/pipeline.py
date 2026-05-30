# worker/pipeline.py
import logging
from dataclasses import dataclass
from pathlib import Path

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
    image_mean_brightness: float    # mean pixel value before normalization [0, 1]


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

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((224, 224), Image.BILINEAR)

        arr = np.array(image, dtype=np.float32) / 255.0   # [0,1]
        image_mean_brightness = float(np.mean(arr))            # capture before normalizing
        arr = (arr - IMAGENET_MEAN) / IMAGENET_STD         # normalize
        arr = arr.transpose(2, 0, 1)                       # HWC → CHW
        arr = np.expand_dims(arr, axis=0)                  # CHW → NCHW (batch=1)
        return arr, image_mean_brightness

    def run(self, image_bytes: bytes) -> InferenceResult:
        input_tensor, image_mean_brightness = self._preprocess(image_bytes)

        outputs = self._session.run(None, {self._input_name: input_tensor})
        logits = outputs[0][0]

        class_id = int(np.argmax(logits))
        confidence = float(np.exp(logits[class_id]) / np.sum(np.exp(logits)))

        logger.info(
            "Inference complete",
            extra={"class_id": class_id, "confidence": round(confidence, 4)},
        )
        return InferenceResult(
            class_id=class_id,
            confidence=confidence,
            image_mean_brightness=image_mean_brightness,
        )