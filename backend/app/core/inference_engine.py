"""YOLO11-seg inference engine with lazy model loading."""

import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

# Make the train/ package importable so that torch pickle can deserialise
# checkpoints that reference train.cbam_module.CBAM — the module path baked
# into the checkpoint during cloud training.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Monkey-patch CBAM into ultralytics.nn.tasks so that checkpoints trained
# with CBAM modules can be deserialised without ultralytics source changes.
# ---------------------------------------------------------------------------
import ultralytics.nn.tasks as _tasks
from app.core.cbam_module import CBAM as _CBAM

_tasks.CBAM = _CBAM


class InferenceEngine:
    """Wraps ultralytics YOLO for standardised inference output.

    Supports lazy loading — the model is only loaded on first ``predict()`` call.

    Usage::

        engine = InferenceEngine("weights/baseline_best.pt")
        result = engine.predict("path/to/image.jpg")
        overlay = engine.visualize("path/to/image.jpg", mode="both")

    Output dict format::

        {
            "boxes": [[x1, y1, x2, y2], ...],      # absolute pixel coords
            "masks": [[[x1,y1], [x2,y2], ...], ...], # normalised poly points
            "scores": [0.95, 0.87, ...],
            "classes": [0, 0, ...],
            "inference_time_ms": 8.5,
            "image_size": [W, H],
        }
    """

    def __init__(self, model_path: str | Path, conf: float = 0.25, iou: float = 0.45):
        self.model_path = str(Path(model_path).resolve())
        self.conf = conf
        self.iou = iou
        self._model = None

    def _load_model(self):
        """Lazy-load the YOLO model."""
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path, task="segment")
        return self._model

    def predict(self, source: str | Path | np.ndarray | Image.Image) -> dict[str, Any]:
        """Run inference on a single image.

        Args:
            source: File path, numpy array (HWC BGR or RGB), or PIL Image.

        Returns:
            Standardised result dict.
        """
        import time
        model = self._load_model()

        t0 = time.perf_counter()
        results = model.predict(source, conf=self.conf, iou=self.iou, verbose=False)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        r = results[0]
        h, w = r.orig_shape if hasattr(r, "orig_shape") else (640, 640)

        boxes: list[list[float]] = []
        masks: list[list[list[float]]] = []
        scores: list[float] = []
        classes: list[int] = []

        if r.boxes is not None:
            for i in range(len(r.boxes)):
                xyxy = r.boxes.xyxy[i].cpu().tolist()
                boxes.append([float(v) for v in xyxy])
                scores.append(float(r.boxes.conf[i]))
                classes.append(int(r.boxes.cls[i]))

        if r.masks is not None:
            for i in range(len(r.masks)):
                poly = r.masks.xy[i]  # normalised [[x,y], ...]
                masks.append(poly.tolist())

        return {
            "boxes": boxes,
            "masks": masks,
            "scores": scores,
            "classes": classes,
            "inference_time_ms": round(elapsed_ms, 2),
            "image_size": [w, h],
        }

    def visualize(
        self,
        source: str | Path | np.ndarray | Image.Image,
        mode: str = "both",
    ) -> Image.Image:
        """Run inference and render overlay.

        Args:
            source: Image source.
            mode: 'box', 'mask', or 'both'.

        Returns:
            PIL Image with rendered annotations.
        """
        from app.core.visualization import visualize_result
        result = self.predict(source)
        return visualize_result(source, result, mode=mode)

    def unload(self):
        """Free model memory."""
        self._model = None
