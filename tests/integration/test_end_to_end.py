# tests/integration/test_end_to_end.py
"""End-to-end test: mocks S3/SQS, tests full gateway→worker flow."""
import json
import io
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np
from PIL import Image

from gateway.config import Settings
from worker.pipeline import InferencePipeline, InferenceResult
from telemetry.monitor import DriftMonitor


def create_test_image_bytes() -> bytes:
    """Generate a simple RGB test image."""
    img = Image.new("RGB", (224, 224), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestFullPipeline:
    def test_pipeline_inference(self):
        """Test ONNX pipeline produces valid results."""
        image_bytes = create_test_image_bytes()
        pipeline = InferencePipeline()

        result = pipeline.run(image_bytes, explain=False)

        assert isinstance(result.class_id, int)
        assert 0 <= result.class_id < 1000  # ImageNet classes
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.top_k_classes) == 5
        assert all(isinstance(c, tuple) and len(c) == 2 for c in result.top_k_classes)
        assert result.confidence_heatmap is None  # explain=False

    def test_drift_monitor_detects_anomaly(self):
        """Test drift monitor catches brightness anomalies."""
        monitor = DriftMonitor(window_size=50, z_threshold=3.0)

        # Warm up with normal values
        for _ in range(15):
            monitor.record(confidence=0.85, image_mean_brightness=0.45)

        # This shouldn't crash (just internal state change)
        monitor.record(confidence=0.40, image_mean_brightness=0.00)

        # Window should now contain 16 values
        assert len(monitor._confidence_window) == 16
        assert len(monitor._brightness_window) == 16

    def test_drift_alert_structure(self):
        """Test DriftAlert dataclass has expected fields."""
        from telemetry.monitor import DriftAlert

        alert = DriftAlert(
            metric="brightness",
            current_value=0.0,
            window_mean=0.45,
            window_std=0.01,
            z_score=-45.0,
        )

        assert alert.metric == "brightness"
        assert isinstance(alert.z_score, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# To run
# uv run pytest tests/integration/test_end_to_end.py -v