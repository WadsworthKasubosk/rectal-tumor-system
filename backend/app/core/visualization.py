"""Visualization: render detection boxes and segmentation masks on images."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


def visualize_result(
    source: str | Path | np.ndarray | Image.Image,
    result: dict[str, Any],
    mode: str = "both",
) -> Image.Image:
    """Overlay detection results on the input image.

    Args:
        source: Input image (path, numpy array, or PIL Image).
        result: Standardised inference result dict.
        mode: 'box' (bounding boxes only), 'mask' (masks only), or 'both'.

    Returns:
        PIL Image in RGB with annotations drawn.
    """
    # Load image as numpy RGB
    if isinstance(source, (str, Path)):
        img = cv2.imread(str(source))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif isinstance(source, np.ndarray):
        img = source
        if img.ndim == 3 and img.shape[2] == 3:
            # Assume BGR if loaded with cv2, try to detect
            pass
    elif isinstance(source, Image.Image):
        img = np.array(source.convert("RGB"))
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    overlay = img.copy()

    color_box = (0, 255, 0)        # green
    color_mask = (255, 0, 0)       # red
    mask_alpha = 0.4

    h, w = img.shape[:2]
    boxes = result.get("boxes", [])
    masks = result.get("masks", [])
    scores = result.get("scores", [])

    # Draw masks first (below boxes)
    if mode in ("mask", "both"):
        mask_layer = np.zeros_like(img)
        for poly in masks:
            if not poly:
                continue
            pts = np.array([(int(p[0] * w), int(p[1] * h)) for p in poly], dtype=np.int32)
            cv2.fillPoly(mask_layer, [pts], color_mask)
        overlay = cv2.addWeighted(overlay, 1.0, mask_layer, mask_alpha, 0)

    # Draw boxes
    if mode in ("box", "both"):
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = [int(v) for v in box]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color_box, 2)
            label = f"{scores[i]:.2f}" if i < len(scores) else "tumor"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(overlay, (x1, y1 - th - 4), (x1 + tw + 4, y1), color_box, -1)
            cv2.putText(overlay, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    return Image.fromarray(overlay)
