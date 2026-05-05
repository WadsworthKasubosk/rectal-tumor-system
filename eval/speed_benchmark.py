"""Measure inference speed of a YOLO11-seg model on GPU and CPU.

Usage:
    python eval/speed_benchmark.py --weights runs/baseline/yolo11s_seg_v1/weights/best.pt
    python eval/speed_benchmark.py --weights yolo11s-seg.pt --runs 50
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("speed_benchmark")


def count_params(model) -> int:
    """Return total number of trainable parameters."""
    return sum(p.numel() for p in model.parameters())


def measure_flops(model, imgsz: int, device: str) -> float:
    """Estimate FLOPs using thop. Returns GFLOPs as float."""
    try:
        from thop import profile
        import torch
        dummy = torch.randn(1, 3, imgsz, imgsz).to(device)
        macs, _ = profile(model, inputs=(dummy,), verbose=False)
        return macs / 1e9
    except ImportError:
        logger.warning("thop not installed — FLOPs set to NaN")
        return float("nan")
    except Exception as e:
        logger.warning("FLOPs estimation failed: %s", e)
        return float("nan")


def benchmark(weights: Path, imgsz: int, warmup: int, runs: int, device: str) -> dict:
    """Run speed benchmark on a given device.

    Returns dict with keys: device, params_m, flops_g, avg_ms, p50_ms, p95_ms, p99_ms, fps.
    """
    import torch
    from ultralytics import YOLO

    logger.info("Benchmarking on %s ...", device)
    device_str = device if device in ("cpu", "cuda") else "cuda" if torch.cuda.is_available() else "cpu"
    if device_str == "cuda":
        device_str = "cuda:0"

    model = YOLO(str(weights))
    model.model.eval()
    model.model.to(device_str)

    # FLOPs
    flops_g = measure_flops(model.model, imgsz, device_str)

    # Parameters
    params_m = count_params(model.model) / 1e6

    # Warmup
    dummy = np.random.randint(0, 255, (imgsz, imgsz, 3), dtype=np.uint8)
    for _ in range(warmup):
        _ = model.predict(dummy, imgsz=imgsz, device=device_str, verbose=False)

    # Timed runs
    latencies: list[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        _ = model.predict(dummy, imgsz=imgsz, device=device_str, verbose=False)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    latencies.sort()
    avg_ms = sum(latencies) / len(latencies)
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    fps = 1000.0 / avg_ms if avg_ms > 0 else 0.0

    return {
        "device": device.upper(),
        "params_m": round(params_m, 2),
        "flops_g": round(flops_g, 2) if not np.isnan(flops_g) else "N/A",
        "avg_ms": round(avg_ms, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "fps": round(fps, 1),
    }


def write_report(results: list[dict], output: Path) -> None:
    """Write benchmark results as a Markdown table."""
    lines = [
        "# Speed Benchmark",
        "",
        f"Model: {results[0].get('model', 'N/A')}" if results else "",
        f"Image size: {results[0].get('imgsz', 'N/A')}" if results else "",
        "",
        "| Device | Params(M) | FLOPs(G) | Avg(ms) | P50(ms) | P95(ms) | P99(ms) | FPS |",
        "|--------|-----------|----------|---------|---------|---------|---------|-----|",
    ]
    for r in results:
        lines.append(
            f"| {r['device']} | {r['params_m']} | {r['flops_g']} | "
            f"{r['avg_ms']} | {r['p50_ms']} | {r['p95_ms']} | {r['p99_ms']} | {r['fps']} |"
        )
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Report written to %s", output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Speed benchmark for YOLO11-seg"
    )
    parser.add_argument("--weights", required=True, type=Path,
                        help="Path to model weights (.pt)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Input image size (default: 640)")
    parser.add_argument("--warmup", type=int, default=10,
                        help="Warmup iterations (default: 10)")
    parser.add_argument("--runs", type=int, default=100,
                        help="Number of timed runs (default: 100)")
    parser.add_argument("--output", type=Path,
                        default=PROJECT_ROOT / "results" / "speed_benchmark.md",
                        help="Output Markdown report path")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.weights.exists():
        logger.error("Weights file not found: %s", args.weights)
        sys.exit(1)

    import torch

    results: list[dict] = []

    # GPU benchmark
    if torch.cuda.is_available():
        r = benchmark(args.weights, args.imgsz, args.warmup, args.runs, "cuda")
        r["model"] = args.weights.name
        r["imgsz"] = args.imgsz
        results.append(r)
    else:
        logger.info("CUDA not available — skipping GPU benchmark")

    # CPU benchmark
    r_cpu = benchmark(args.weights, args.imgsz, min(args.warmup, 3), min(args.runs, 20), "cpu")
    r_cpu["model"] = args.weights.name
    r_cpu["imgsz"] = args.imgsz
    results.append(r_cpu)

    write_report(results, args.output)

    # Print summary
    logger.info("=" * 50)
    for r in results:
        logger.info(
            "%s | Params: %.1fM | FLOPs: %sG | Avg: %.1fms | FPS: %.1f",
            r["device"], r["params_m"], r["flops_g"], r["avg_ms"], r["fps"],
        )


if __name__ == "__main__":
    main()
