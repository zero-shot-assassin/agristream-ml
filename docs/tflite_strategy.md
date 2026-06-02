# TFLite Edge Conversion Strategy

## Use Case
Field devices in areas with zero cellular coverage need offline inference.

## Conversion Path
1. ONNX → TensorFlow SavedModel (onnx2tf)
2. TensorFlow SavedModel → TFLite (TFLite Converter)
3. TFLite → Quantized INT8 (post-training quantization for 4x smaller, 2-3x faster)

## Runtime Options
- **Android/iOS**: TensorFlow Lite mobile SDK
- **Raspberry Pi**: tflite_runtime (Python, no full TF dependency)
- **Microcontrollers**: TFLite for Microcontrollers (C++), though MobileNetV3 may be too large

## Trade-offs
- INT8 quantization: ~1-2% accuracy loss vs 4x size reduction
- No telemetry/drift detection (offline) — batch logs for upload when connected
- Model updates require physical access or local Wi-Fi sync