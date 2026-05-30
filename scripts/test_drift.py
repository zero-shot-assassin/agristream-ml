# scripts/test_drift.py
import logging
logging.basicConfig(level=logging.WARNING)

from telemetry.monitor import DriftMonitor

m = DriftMonitor(window_size=50, z_threshold=3.0)

for i in range(15):
    m.record(confidence=0.85, image_mean_brightness=0.45)

print("Injecting black image...")
m.record(confidence=0.40, image_mean_brightness=0.0)
print("Done.")

# run: PYTHONPATH=. uv run python scripts/test_drift.py