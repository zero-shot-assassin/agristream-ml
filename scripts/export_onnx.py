# scripts/export_onnx.py
from pathlib import Path
 
import torch
import torchvision.models as models

OUTPUT_PATH = Path("models/mobilenetv3.onnx")
OUTPUT_PATH.parent.mkdir(exist_ok=True)
 
model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
model.eval()

dummy_input = torch.randn(1, 3, 224, 224)
 
torch.onnx.export(
    model,
    dummy_input,
    str(OUTPUT_PATH),
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    opset_version=18,
)
 
print(f"Exported model to {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / 1024:.1f} KB)")