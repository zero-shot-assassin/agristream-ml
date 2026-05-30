# telemetry/monitor.py
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

import numpy as np

logger = logging.getLogger("agristream.telemetry")


@dataclass
class DriftAlert:
    metric: str
    current_value: float
    window_mean: float
    window_std: float
    z_score: float


class DriftMonitor:
    def __init__(self, window_size: int = 50, z_threshold: float = 3.0) -> None:
        self._window_size = window_size
        self._z_threshold = z_threshold

        # Concept drift — tracks model confidence scores
        self._confidence_window: Deque[float] = deque(maxlen=window_size)

        # Data drift — tracks mean pixel brightness of raw images
        self._brightness_window: Deque[float] = deque(maxlen=window_size)

    def record(self, confidence: float, image_mean_brightness: float) -> None:
        self._confidence_window.append(confidence)
        self._brightness_window.append(image_mean_brightness)

        self._check_drift("confidence", self._confidence_window, confidence)
        self._check_drift("brightness", self._brightness_window, image_mean_brightness)

    def _check_drift(
        self,
        metric: str,
        window: Deque[float],
        current_value: float,
    ) -> None:
        if len(window) < 10:
            return                          # need minimum observations first

        values = np.array(window, dtype=np.float32)
        mean = float(np.mean(values))
        std = max(float(np.std(values)), 1e-3)   # floor prevents division by zero but allows detection

        if std < 1e-6:
            return                          # no variance yet — avoid division by zero

        z_score = (current_value - mean) / std

        if abs(z_score) > self._z_threshold:
            alert = DriftAlert(
                metric=metric,
                current_value=round(current_value, 4),
                window_mean=round(mean, 4),
                window_std=round(std, 4),
                z_score=round(z_score, 4),
            )
            logger.warning(
                "DRIFT DETECTED | metric=%s | current=%.4f | mean=%.4f | std=%.4f | z=%.4f",
                alert.metric,
                alert.current_value,
                alert.window_mean,
                alert.window_std,
                alert.z_score,
            )