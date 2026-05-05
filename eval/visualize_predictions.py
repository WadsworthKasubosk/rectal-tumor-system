"""Generate 3-panel visualizations (Original / GT / Prediction) for qualitative review.

For each test subset, randomly samples images and creates:
  - Individual 3-panel comparison images
  - A vertically stacked grid overview

Usage:
    python eval/visualize_predictions.py --weights runs/baseline/yolo11s_seg_v1/weights/best.pt
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "datasets" / "rectal_tumor"
SUBSETS: list[str] = [
    "CVC-300",
    "CVC-ClinicDB",
    "CVC-ColonDB",
    "ETIS-LaribPolypDB",
    "Kvasir",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("visualize")

# Color constants (BGR for OpenCV)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def parse_yolo_label(label_path: Path) -> list[list[tuple[float, float]]]:
    """Parse a YOLO-seg label into list of polygons (normalized coords)."""
    polygons: list[list[tuple[float, float]]] = []
    if not label_path.exists():
        return polygons
    for line in label_path.read_text(encoding="utf-8").strip().splitlines():
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        coords = [float(x) for x in parts[1:]]
        pts = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
        polygons.append(pts)
    return polygons


def draw_mask_overlay(
    img: np.ndarray,
    polygons: list[list[tuple[float, float]]],
    color: tuple[int, int, int],
    alpha: float = 0.4,
) -> np.ndarray:
    """Draw semi-transparent mask overlay from polygon list."""
    overlay = img.copy()
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    for poly in polygons:
        pts = np.array([(int(x * w), int(y * h)) for x, y in poly], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
    overlay[mask > 0] = color
    return cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)


def draw_bboxes(
    img: np.ndarray,
    polygons: list[list[tuple[float, float]]],
    color: tuple[int, int, int],
    thickness: int = 2,
) -> np.ndarray:
    """Draw bounding boxes with confidence scores."""
    h, w = img.shape[:2]
    for poly in polygons:
        pts = np.array([(int(x * w), int(y * h)) for x, y in poly], dtype=np.int32)
        x1, y1 = pts.min(axis=0)
        x2, y2 = pts.max(axis=0)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    return img


def compute_dice_from_polygons(
    gt_polygons: list[list[tuple[float, float]]],
    pred_polygons: list[list[tuple[float, float]]],
    h: int, w: int,
) -> float:
    """Compute Dice score from polygon lists."""
    gt_mask = np.zeros((h, w), dtype=np.uint8)
    pred_mask = np.zeros((h, w), dtype=np.uint8)
    for poly in gt_polygons:
        pts = np.array([(int(x * w), int(y * h)) for x, y in poly], dtype=np.int32)
        cv2.fillPoly(gt_mask, [pts], 255)
    for poly in pred_polygons:
        pts = np.array([(int(x * w), int(y * h)) for x, y in poly], dtype=np.int32)
        cv2.fillPoly(pred_mask, [pts], 255)
    gt_b = gt_mask > 127
    pred_b = pred_mask > 127
    inter = np.logical_and(gt_b, pred_b).sum()
    denom = gt_b.sum() + pred_b.sum()
    return float(2 * inter / denom) if denom > 0 else 0.0


def get_pred_polygons(result, h: int, w: int) -> list[list[tuple[float, float]]]:
    """Convert YOLO prediction masks to normalized polygon list."""
    polygons: list[list[tuple[float, float]]] = []
    if result.masks is None:
        return polygons
    for i in range(len(result.masks.data)):
        mask = result.masks.data[i].cpu().numpy()
        mask_resized = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
        binary = (mask_resized > 0.5).astype(np.uint8) * 255
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 10:
                continue
            approx = cnt.squeeze(axis=1)
            if approx.ndim != 2 or len(approx) < 3:
                continue
            norm = [(float(p[0]) / w, float(p[1]) / h) for p in approx]
            polygons.append(norm)
    return polygons


def visualize_subset(
    model: YOLO,
    subset: str,
    data_root: Path,
    num_samples: int,
    output_root: Path,
    conf: float,
    seed: int,
) -> None:
    """Create visualizations for a single test subset."""
    img_dir = data_root / "images" / "test" / subset
    label_dir = data_root / "labels" / "test" / subset
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    image_files = sorted([f for f in img_dir.glob("*")
                          if f.is_file() and f.suffix.lower() in valid_exts])

    if not image_files:
        logger.warning("No images found for %s", subset)
        return

    rng = random.Random(seed)
    samples = rng.sample(image_files, min(num_samples, len(image_files)))

    subset_out = output_root / subset
    subset_out.mkdir(parents=True, exist_ok=True)

    panels: list[np.ndarray] = []

    for img_path in samples:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        panel_h = h + 30  # 30px header

        # --- GT ---
        gt_polygons = parse_yolo_label(label_dir / f"{img_path.stem}.txt")
        gt_overlay = draw_mask_overlay(img.copy(), gt_polygons, GREEN, alpha=0.4)
        gt_overlay = draw_bboxes(gt_overlay, gt_polygons, GREEN, thickness=2)

        # --- Prediction ---
        results = model.predict(img, conf=conf, verbose=False)
        pred_polygons = get_pred_polygons(results[0], h, w) if len(results) > 0 else []
        pred_overlay = draw_mask_overlay(img.copy(), pred_polygons, RED, alpha=0.4)
        pred_overlay = draw_bboxes(pred_overlay, pred_polygons, RED, thickness=2)

        # Draw confidence scores on prediction boxes
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                score = float(box.conf[0])
                cv2.rectangle(pred_overlay, (x1, y1), (x2, y2), RED, 2)
                cv2.putText(pred_overlay, f"{score:.2f}", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, RED, 2)

        dice = compute_dice_from_polygons(gt_polygons, pred_polygons, h, w)

        # --- Build 3-panel ---
        panel = np.zeros((panel_h, w * 3, 3), dtype=np.uint8)
        panel[:30, :] = WHITE
        cv2.putText(panel, f"{img_path.name}  |  Dice: {dice:.4f}", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 2)

        panel[30:30 + h, 0:w] = img
        panel[30:30 + h, w:2 * w] = gt_overlay
        panel[30:30 + h, 2 * w:3 * w] = pred_overlay

        # Label columns
        for col, label in [(0, "Original"), (w, "Ground Truth"), (2 * w, "Prediction")]:
            cv2.putText(panel, label, (col + 10, panel_h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

        # Save individual
        out_path = subset_out / img_path.name
        cv2.imwrite(str(out_path), panel)
        panels.append(panel)
        logger.info("  %s / %s (Dice=%.4f)", subset, img_path.name, dice)

    # --- Build grid (vertical stack) ---
    if panels:
        grid = np.vstack(panels)
        cv2.imwrite(str(subset_out / "grid.jpg"), grid)
        logger.info("  -> grid.jpg saved (%d panels)", len(panels))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate 3-panel visualizations for qualitative analysis"
    )
    parser.add_argument("--weights", required=True, type=Path,
                        help="Path to model weights")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT,
                        help="Dataset root (default: datasets/rectal_tumor)")
    parser.add_argument("--num-samples", type=int, default=8,
                        help="Number of samples per subset (default: 8)")
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "results" / "visualizations",
                        help="Output directory")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="Confidence threshold (default: 0.25)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.weights.exists():
        logger.error("Weights not found: %s", args.weights)
        sys.exit(1)

    model = YOLO(str(args.weights))

    for subset in SUBSETS:
        img_dir = args.data_root / "images" / "test" / subset
        if not img_dir.exists():
            logger.warning("Skipping %s — directory not found", subset)
            continue
        logger.info("Visualizing %s ...", subset)
        visualize_subset(
            model, subset, args.data_root, args.num_samples, args.output_dir,
            args.conf, args.seed,
        )

    logger.info("All visualizations saved to %s", args.output_dir)


if __name__ == "__main__":
    main()
