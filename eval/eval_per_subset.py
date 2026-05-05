"""Evaluate YOLO11-seg on each test subset independently.

Computes YOLO metrics (box/mask mAP, P, R) via model.val(), plus
per-sample Dice and mIoU.  Outputs a Markdown table, CSV, and rich
terminal display.

Usage:
    python eval/eval_per_subset.py --weights runs/baseline/yolo11s_seg_v1/weights/best.pt
"""

from __future__ import annotations

import argparse
import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Make the project root importable so torch pickle can resolve train.cbam_module
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np
import torch
import yaml
from rich.console import Console
from rich.table import Table

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
logger = logging.getLogger("eval_per_subset")


def _make_temp_yaml(data_root: Path, subset: str) -> Path:
    """Create a temporary dataset YAML for a specific test subset."""
    content = {
        "path": str(data_root.resolve()),
        "train": "images/train",
        "val": f"images/test/{subset}",
        "names": {0: "tumor"},
        "nc": 1,
    }
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8")
    yaml.safe_dump(content, tmp)
    return Path(tmp.name)


def _compute_dice_iou(
    pred_mask: np.ndarray | None, gt_mask: np.ndarray
) -> tuple[float, float]:
    """Compute Dice and IoU for a single (pred, GT) mask pair.

    If pred_mask is None (no prediction), returns (0.0, 0.0).
    """
    if pred_mask is None or pred_mask.sum() == 0:
        if gt_mask.sum() == 0:
            return 1.0, 1.0  # both empty → perfect match
        return 0.0, 0.0

    gt = gt_mask.astype(bool)
    pred = pred_mask.astype(bool)
    intersection = np.logical_and(pred, gt).sum()
    union = np.logical_or(pred, gt).sum()
    dice = 2 * intersection / (pred.sum() + gt.sum()) if (pred.sum() + gt.sum()) > 0 else 0.0
    iou = intersection / union if union > 0 else 0.0
    return float(dice), float(iou)


def _get_pred_mask(result, img_h: int, img_w: int) -> np.ndarray | None:
    """Extract combined prediction mask from a YOLO result for a single image."""
    if result.masks is None:
        return None
    try:
        combined = np.zeros((img_h, img_w), dtype=np.uint8)
        for i in range(len(result.masks.data)):
            mask = result.masks.data[i].cpu().numpy()
            # Resize mask to original image size
            import cv2
            mask_resized = cv2.resize(mask, (img_w, img_h), interpolation=cv2.INTER_LINEAR)
            combined = np.maximum(combined, (mask_resized * 255).astype(np.uint8))
        return (combined > 127).astype(np.uint8)
    except Exception:
        return None


def evaluate_subset(
    weights: Path,
    data_root: Path,
    subset: str,
    imgsz: int,
    batch: int,
    device: str,
    conf: float,
    iou: float,
) -> dict:
    """Evaluate model on a single test subset. Returns metrics dict."""
    from ultralytics import YOLO
    import cv2

    logger.info("--- %s ---", subset)
    tmp_yaml = _make_temp_yaml(data_root, subset)

    model = YOLO(str(weights))
    val_results = model.val(
        data=str(tmp_yaml),
        split="val",
        imgsz=imgsz,
        batch=batch,
        device=device,
        conf=conf,
        iou=iou,
        save_json=False,
        verbose=False,
    )

    # Safely dispose temp yaml
    try:
        tmp_yaml.unlink()
    except OSError:
        pass

    # Extract YOLO metrics
    box_map50 = float(val_results.box.map50) if val_results.box is not None else 0.0
    box_map = float(val_results.box.map) if val_results.box is not None else 0.0
    box_p = float(val_results.box.mp) if val_results.box is not None else 0.0
    box_r = float(val_results.box.mr) if val_results.box is not None else 0.0

    seg_map50 = float(val_results.seg.map50) if hasattr(val_results, 'seg') and val_results.seg is not None else 0.0
    seg_map = float(val_results.seg.map) if hasattr(val_results, 'seg') and val_results.seg is not None else 0.0
    seg_p = float(val_results.seg.mp) if hasattr(val_results, 'seg') and val_results.seg is not None else 0.0
    seg_r = float(val_results.seg.mr) if hasattr(val_results, 'seg') and val_results.seg is not None else 0.0

    # Per-sample Dice / mIoU
    img_dir = data_root / "images" / "test" / subset
    label_dir = data_root / "labels" / "test" / subset
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    image_files = sorted([f for f in img_dir.glob("*")
                          if f.is_file() and f.suffix.lower() in valid_exts])

    dice_scores: list[float] = []
    iou_scores: list[float] = []
    times_ms: list[float] = []

    for img_path in image_files:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]

        # Inference
        import time
        t0 = time.perf_counter()
        results = model.predict(img, imgsz=imgsz, device=device, conf=conf, iou=iou, verbose=False)
        elapsed = (time.perf_counter() - t0) * 1000.0
        times_ms.append(elapsed)

        # Load GT mask
        lbl_path = label_dir / f"{img_path.stem}.txt"
        gt_mask = np.zeros((h, w), dtype=np.uint8)
        if lbl_path.exists():
            for line in lbl_path.read_text(encoding="utf-8").strip().splitlines():
                parts = line.strip().split()
                if len(parts) < 7:
                    continue
                pts_flat = [float(x) for x in parts[1:]]
                pts = np.array([(pts_flat[i] * w, pts_flat[i + 1] * h)
                               for i in range(0, len(pts_flat), 2)], dtype=np.int32)
                cv2.fillPoly(gt_mask, [pts], 255)

        # Prediction mask
        pred_mask = _get_pred_mask(results[0], h, w) if len(results) > 0 else None

        d, iou_val = _compute_dice_iou(pred_mask, gt_mask)
        dice_scores.append(d)
        iou_scores.append(iou_val)

    mean_dice = float(np.mean(dice_scores)) if dice_scores else 0.0
    mean_iou = float(np.mean(iou_scores)) if iou_scores else 0.0
    mean_fps = 1000.0 / (sum(times_ms) / len(times_ms)) if times_ms else 0.0

    result = {
        "subset": subset,
        "box_map50": round(box_map50, 4),
        "box_map": round(box_map, 4),
        "box_p": round(box_p, 4),
        "box_r": round(box_r, 4),
        "seg_map50": round(seg_map50, 4),
        "seg_map": round(seg_map, 4),
        "seg_p": round(seg_p, 4),
        "seg_r": round(seg_r, 4),
        "dice": round(mean_dice, 4),
        "miou": round(mean_iou, 4),
        "fps": round(mean_fps, 1),
        "n_images": len(image_files),
    }
    logger.info(
        "  Box mAP50=%.4f  Mask mAP50=%.4f  Dice=%.4f  mIoU=%.4f  FPS=%.1f",
        result["box_map50"], result["seg_map50"], result["dice"], result["miou"], result["fps"],
    )
    return result


def write_reports(all_metrics: list[dict], output_dir: Path) -> None:
    """Write per_subset_metrics.md and .csv."""
    output_dir.mkdir(parents=True, exist_ok=True)

    headers = [
        "Subset", "Box_mAP50", "Box_mAP50-95", "Mask_mAP50", "Mask_mAP50-95",
        "Precision", "Recall", "Dice", "mIoU", "FPS",
    ]

    # CSV
    csv_lines = [",".join(headers)]
    for m in all_metrics:
        csv_lines.append(
            f"{m['subset']},{m['box_map50']},{m['box_map']},{m['seg_map50']},{m['seg_map']},"
            f"{m['seg_p']},{m['seg_r']},{m['dice']},{m['miou']},{m['fps']}"
        )
    # Mean row
    means = {}
    for k in headers[1:]:
        key = {"Box_mAP50": "box_map50", "Box_mAP50-95": "box_map",
               "Mask_mAP50": "seg_map50", "Mask_mAP50-95": "seg_map",
               "Precision": "seg_p", "Recall": "seg_r",
               "Dice": "dice", "mIoU": "miou", "FPS": "fps"}[k]
        vals = [m[key] for m in all_metrics]
        means[k] = round(sum(vals) / len(vals), 4) if vals else 0.0
    csv_lines.append(
        f"Mean,{means['Box_mAP50']},{means['Box_mAP50-95']},"
        f"{means['Mask_mAP50']},{means['Mask_mAP50-95']},"
        f"{means['Precision']},{means['Recall']},"
        f"{means['Dice']},{means['mIoU']},{means['FPS']}"
    )
    (output_dir / "per_subset_metrics.csv").write_text("\n".join(csv_lines), encoding="utf-8")

    # Markdown
    md_lines = [
        "# Per-Subset Evaluation Metrics",
        "",
        f"Evaluated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"| {' | '.join(headers)} |",
        f"|{'|'.join(['---'] * len(headers))}|",
    ]
    for m in all_metrics:
        md_lines.append(
            f"| {m['subset']} | {m['box_map50']} | {m['box_map']} | "
            f"{m['seg_map50']} | {m['seg_map']} | {m['seg_p']} | {m['seg_r']} | "
            f"{m['dice']} | {m['miou']} | {m['fps']} |"
        )
    md_lines.append(
        f"| **Mean** | {means['Box_mAP50']} | {means['Box_mAP50-95']} | "
        f"{means['Mask_mAP50']} | {means['Mask_mAP50-95']} | "
        f"{means['Precision']} | {means['Recall']} | "
        f"{means['Dice']} | {means['mIoU']} | {means['FPS']} |"
    )
    md_lines.append("")
    (output_dir / "per_subset_metrics.md").write_text("\n".join(md_lines), encoding="utf-8")


def print_rich_table(all_metrics: list[dict]) -> None:
    """Display results with rich.table."""
    console = Console()
    table = Table(title="Per-Subset Evaluation Results", title_style="bold cyan")

    columns = ["Subset", "Box mAP50", "Box mAP", "Mask mAP50", "Mask mAP",
               "P", "R", "Dice", "mIoU", "FPS"]
    for col in columns:
        table.add_column(col, justify="right" if col != "Subset" else "left")

    for m in all_metrics:
        table.add_row(
            m["subset"], str(m["box_map50"]), str(m["box_map"]),
            str(m["seg_map50"]), str(m["seg_map"]),
            str(m["seg_p"]), str(m["seg_r"]),
            str(m["dice"]), str(m["miou"]), str(m["fps"]),
        )

    # Mean
    n = len(all_metrics)
    table.add_row(
        "Mean",
        str(round(sum(m["box_map50"] for m in all_metrics) / n, 4)),
        str(round(sum(m["box_map"] for m in all_metrics) / n, 4)),
        str(round(sum(m["seg_map50"] for m in all_metrics) / n, 4)),
        str(round(sum(m["seg_map"] for m in all_metrics) / n, 4)),
        str(round(sum(m["seg_p"] for m in all_metrics) / n, 4)),
        str(round(sum(m["seg_r"] for m in all_metrics) / n, 4)),
        str(round(sum(m["dice"] for m in all_metrics) / n, 4)),
        str(round(sum(m["miou"] for m in all_metrics) / n, 4)),
        str(round(sum(m["fps"] for m in all_metrics) / n, 1)),
        style="bold",
    )
    console.print(table)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate YOLO11-seg on 5 test subsets"
    )
    parser.add_argument("--weights", required=True, type=Path,
                        help="Path to best.pt weights")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT,
                        help="Root of YOLO dataset (default: datasets/rectal_tumor)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Input image size (default: 640)")
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size (default: 16)")
    parser.add_argument("--device", default="0",
                        help="Device (default: 0)")
    parser.add_argument("--conf", type=float, default=0.001,
                        help="Confidence threshold for evaluation (default: 0.001)")
    parser.add_argument("--iou", type=float, default=0.6,
                        help="IoU threshold (default: 0.6)")
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "results",
                        help="Output directory for reports")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.weights.exists():
        logger.error("Weights not found: %s", args.weights)
        sys.exit(1)

    all_metrics: list[dict] = []
    for subset in SUBSETS:
        img_dir = args.data_root / "images" / "test" / subset
        if not img_dir.exists():
            logger.warning("Subset directory not found: %s — skipping", img_dir)
            continue
        m = evaluate_subset(
            args.weights, args.data_root, subset,
            args.imgsz, args.batch, args.device, args.conf, args.iou,
        )
        all_metrics.append(m)

    if not all_metrics:
        logger.error("No subsets evaluated")
        sys.exit(1)

    write_reports(all_metrics, args.output_dir)
    print_rich_table(all_metrics)
    logger.info("Reports written to %s", args.output_dir)


if __name__ == "__main__":
    main()
