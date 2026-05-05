"""Train YOLO11s-seg baseline for rectal tumor segmentation.

Usage:
    python train/train_baseline.py
    python train/train_baseline.py --epochs 300 --batch 32 --device 0

Hyperparameters are hardcoded for reproducibility. After training completes,
this script automatically runs eval_per_subset.py and speed_benchmark.py
on the best checkpoint.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = Path.cwd() / "logs"  # cwd is writable on Kaggle (/kaggle/working/)
LOG_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ---------------------------------------------------------------------------
# logger
# ---------------------------------------------------------------------------
logger = logging.getLogger("train_baseline")
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler(LOG_DIR / f"train_baseline_{TIMESTAMP}.log", encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(fh)

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(ch)

# ---------------------------------------------------------------------------
# hardcoded training hyperparams
# ---------------------------------------------------------------------------
HYPERPARAMS: dict = {
    "optimizer": "AdamW",
    "lr0": 0.001,
    "lrf": 0.01,
    "cos_lr": True,
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 3,
    "warmup_momentum": 0.8,
    "patience": 30,
    "close_mosaic": 10,
    "mosaic": 1.0,
    "mixup": 0.1,
    "copy_paste": 0.1,
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,
    "degrees": 10,
    "translate": 0.1,
    "scale": 0.5,
    "fliplr": 0.5,
    "flipud": 0.0,
    "save": True,
    "save_period": 20,
    "plots": True,
    "val": True,
    "amp": True,
    "seed": 42,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train YOLO11s-seg baseline for rectal tumor segmentation"
    )
    parser.add_argument("--model", default="yolo11s-seg.pt",
                        help="Base model / checkpoint path (default: yolo11s-seg.pt)")
    parser.add_argument("--data", default=str(PROJECT_ROOT / "configs" / "rectal_tumor.yaml"),
                        help="Dataset YAML path")
    parser.add_argument("--epochs", type=int, default=200,
                        help="Number of training epochs (default: 200)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Input image size (default: 640)")
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size (default: 16)")
    parser.add_argument("--device", default="0",
                        help="Device: 0 for GPU, cpu for CPU (default: 0)")
    parser.add_argument("--project", default="runs/baseline",
                        help="W&B-like project directory (default: runs/baseline)")
    parser.add_argument("--name", default="yolo11s_seg_v1",
                        help="Experiment name (default: yolo11s_seg_v1)")
    parser.add_argument("--resume", action="store_true", default=False,
                        help="Resume from last checkpoint")
    parser.add_argument("--no-post", action="store_true", default=False,
                        help="Skip post-training eval and benchmark (useful for Kaggle)")
    return parser


def train(args: argparse.Namespace) -> Path:
    """Run training and return path to best.pt."""
    logger.info("=== Training Configuration ===")
    logger.info("Model:       %s", args.model)
    logger.info("Data:        %s", args.data)
    logger.info("Epochs:      %d", args.epochs)
    logger.info("Image size:  %d", args.imgsz)
    logger.info("Batch size:  %d", args.batch)
    logger.info("Device:      %s", args.device)
    logger.info("Project:     %s", args.project)
    logger.info("Experiment:  %s", args.name)
    logger.info("Hyperparams: %s", HYPERPARAMS)
    logger.info("=" * 50)

    model = YOLO(args.model)

    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
        **HYPERPARAMS,
    )

    best_pt = Path(results.save_dir) / "weights" / "best.pt"
    if not best_pt.exists():
        logger.error("best.pt not found at %s — training may have failed", best_pt)
        sys.exit(1)

    logger.info("Training complete. best.pt: %s", best_pt)
    return best_pt


def run_eval(best_pt: Path) -> None:
    """Launch eval_per_subset.py on the trained weights."""
    script = PROJECT_ROOT / "eval" / "eval_per_subset.py"
    logger.info("=== Running per-subset evaluation ===")
    cmd = [
        sys.executable, str(script),
        "--weights", str(best_pt),
    ]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        logger.warning("eval_per_subset exited with code %d", result.returncode)


def run_benchmark(best_pt: Path) -> None:
    """Launch speed_benchmark.py on the trained weights."""
    script = PROJECT_ROOT / "eval" / "speed_benchmark.py"
    logger.info("=== Running speed benchmark ===")
    cmd = [
        sys.executable, str(script),
        "--weights", str(best_pt),
    ]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        logger.warning("speed_benchmark exited with code %d", result.returncode)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    best_pt = train(args)

    if not args.no_post:
        logger.info("=== Post-training evaluation ===")
        run_eval(best_pt)
        run_benchmark(best_pt)
    else:
        logger.info("=== Skipping post-training evaluation (--no-post) ===")

    logger.info("=== All done ===")
    logger.info("best.pt:          %s", best_pt)
    logger.info("Per-subset metrics: results/per_subset_metrics.md")
    logger.info("Speed benchmark:    results/speed_benchmark.md")


if __name__ == "__main__":
    main()
