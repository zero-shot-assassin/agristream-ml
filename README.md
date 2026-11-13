# AgriStream ML

Production-grade async ML pipeline for agricultural image analysis on AWS.

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│  Field      │────▶│  FastAPI │────▶│   S3    │     │   SQS    │
│  Device     │     │  Gateway │     │ Images  │     │  Queue   │
└─────────────┘     └──────────┘     └─────────┘     └────┬─────┘
                                                            │
                       ┌────────────────────────────────────┘
                       ▼
                ┌─────────────┐
                │ ECS Worker  │ ──► ONNX Runtime inference
                │ (Fargate)   │ ──► Drift monitoring
                └─────────────┘ ──► XAI explanations (optional)
```

## Key Features

| Component | Technology | Production Pattern |
|-----------|-----------|-------------------|
| Gateway | FastAPI | Streaming S3 upload, async SQS enqueue |
| Worker | ONNX Runtime | Singleton model, thread-safe inference |
| Drift Detection | Rolling Z-score | Confidence + brightness anomaly detection |
| XAI | Patch heatmaps | Model-agnostic explainability |
| Infra | Terraform | Modular S3/SQS/ECS with least-privilege IAM |
| Edge Strategy | TFLite | INT8 quantized for offline devices |

## Quick Start

```bash
# Setup
uv pip install -e .

# Run gateway
uv run uvicorn gateway.app:app --reload

# Run worker (separate terminal)
uv run python -m worker.main

# Test
curl -X POST http://localhost:8000/v1/upload -F "file=@image.jpg"

# Integration tests
uv run pytest tests/integration/ -v
```

## Environment Variables

```bash
AWS_REGION=us-east-1
AGRISTREAM_S3_BUCKET=your-bucket
AGRISTREAM_SQS_QUEUE_URL=https://sqs...
AWS_ACCESS_KEY_ID=xxx  # local dev only; use IAM roles in production
AWS_SECRET_ACCESS_KEY=xxx
```

## License

MIT — Portfolio demonstration project.
