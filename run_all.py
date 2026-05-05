"""One-click pipeline: train → evaluate → visualize → benchmark.

Usage:
    python run_all.py
    python run_all.py --epochs 100 --batch 8
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("run_all")


def find_best_pt(project: str, name: str) -> Path:
    """Locate best.pt after training."""
    candidates = [
        PROJECT_ROOT / project / name / "weights" / "best.pt",
        PROJECT_ROOT / "runs" / "baseline" / "yolo11s_seg_v1" / "weights" / "best.pt",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fallback: search
    for p in sorted(PROJECT_ROOT.rglob("best.pt"), reverse=True):
        return p
    raise FileNotFoundError("Cannot find best.pt in runs/")


def run_step(name: str, cmd: list[str]) -> float:
    """Run a pipeline step. Returns elapsed seconds. Exits on failure."""
    logger.info("=" * 60)
    logger.info("STEP: %s", name)
    logger.info("Command: %s", " ".join(cmd))
    t0 = time.perf_counter()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = time.perf_counter() - t0
    if result.returncode != 0:
        logger.error("Step '%s' FAILED with exit code %d", name, result.returncode)
        logger.error("Previous steps' outputs are preserved.")
        sys.exit(result.returncode)
    logger.info("Step '%s' completed in %.0f seconds", name, elapsed)
    return elapsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-click training + evaluation pipeline"
    )
    parser.add_argument("--epochs", type=int, default=200,
                        help="Training epochs (default: 200)")
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size (default: 16)")
    parser.add_argument("--device", default="0",
                        help="Device (default: 0)")
    parser.add_argument("--model", default="yolo11s-seg.pt",
                        help="Base model (default: yolo11s-seg.pt)")
    parser.add_argument("--skip-train", action="store_true",
                        help="Skip training (use existing best.pt)")
    parser.add_argument("--weights", type=Path, default=None,
                        help="Path to weights (skips training if provided)")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    start_time = time.perf_counter()
    artifacts: list[str] = []

    # --- Determine weights ---
    if args.weights:
        best_pt = args.weights.resolve()
        logger.info("Using provided weights: %s", best_pt)
    elif args.skip_train:
        best_pt = find_best_pt("runs/baseline", "yolo11s_seg_v1")
        logger.info("Using existing weights: %s", best_pt)
    else:
        # Step 1: Train
        train_script = PROJECT_ROOT / "train" / "train_baseline.py"
        train_cmd = [
            sys.executable, str(train_script),
            "--epochs", str(args.epochs),
            "--batch", str(args.batch),
            "--device", args.device,
            "--model", args.model,
            "--no-post",  # run_all handles eval/benchmark separately
        ]
        train_elapsed = run_step("Train Baseline", train_cmd)
        artifacts.append(f"Training artifacts: runs/baseline/yolo11s_seg_v1/")

        best_pt = find_best_pt("runs/baseline", "yolo11s_seg_v1")
        logger.info("Training duration: %.0f min", train_elapsed / 60)

    if not best_pt.exists():
        logger.error("best.pt not found at %s", best_pt)
        sys.exit(1)

    artifacts.append(f"best.pt: {best_pt}")
    logger.info("Weights: %s", best_pt)

    # Step 2: Evaluate
    eval_script = PROJECT_ROOT / "eval" / "eval_per_subset.py"
    eval_cmd = [
        sys.executable, str(eval_script),
        "--weights", str(best_pt),
    ]
    run_step("Per-Subset Evaluation", eval_cmd)
    artifacts.append("Metrics: results/per_subset_metrics.md")
    artifacts.append("Metrics: results/per_subset_metrics.csv")

    # Step 3: Visualize
    vis_script = PROJECT_ROOT / "eval" / "visualize_predictions.py"
    vis_cmd = [
        sys.executable, str(vis_script),
        "--weights", str(best_pt),
    ]
    run_step("Visualizations", vis_cmd)
    artifacts.append("Visualizations: results/visualizations/")

    # Step 4: Speed benchmark
    bench_script = PROJECT_ROOT / "eval" / "speed_benchmark.py"
    bench_cmd = [
        sys.executable, str(bench_script),
        "--weights", str(best_pt),
    ]
    run_step("Speed Benchmark", bench_cmd)
    artifacts.append("Benchmark: results/speed_benchmark.md")

    # Summary
    total_elapsed = time.perf_counter() - start_time
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("Total duration: %.0f min (%.1f hours)",
                total_elapsed / 60, total_elapsed / 3600)
    logger.info("")
    logger.info("Artifacts:")
    for a in artifacts:
        logger.info("  - %s", a)


if __name__ == "__main__":
    main()
