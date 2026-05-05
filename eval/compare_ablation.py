"""Compare ablation experiment results across model variants.

Evaluates each experiment on all 5 test subsets and produces:
  - results/ablation_table.md  (Markdown comparison)
  - results/ablation_table.csv  (CSV comparison)
  - results/ablation_chart.png  (bar chart of Dice scores)

Usage:
    python eval/compare_ablation.py \\
        --runs baseline:yolo11s_seg_v1 p2:exp2_p2 cbam:exp3_cbam p2_cbam:exp4_p2_cbam
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = PROJECT_ROOT / "runs" / "segment"
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
logger = logging.getLogger("compare_ablation")


def _find_best_pt(run_dir: str) -> Path:
    """Locate best.pt given an experiment name or path.

    Tries:
      1. <run_dir> as an absolute/relative path to best.pt
      2. runs/segment/<run_dir>/weights/best.pt
      3. runs/segment/runs/baseline/<run_dir>/weights/best.pt  (legacy baseline layout)
    """
    candidate = Path(run_dir)
    if candidate.is_file() and candidate.suffix == ".pt":
        return candidate.resolve()

    for base in [
        RUNS_ROOT / run_dir,
        RUNS_ROOT / "runs" / "baseline" / run_dir,
    ]:
        pt = base / "weights" / "best.pt"
        if pt.exists():
            return pt.resolve()

    raise FileNotFoundError(f"Cannot find best.pt for run '{run_dir}'")


def evaluate_single(best_pt: Path) -> list[dict]:
    """Run eval_per_subset's evaluate_subset on each subset. Returns list of metric dicts."""
    from eval.eval_per_subset import evaluate_subset, DATA_ROOT

    all_metrics: list[dict] = []
    for subset in SUBSETS:
        img_dir = DATA_ROOT / "images" / "test" / subset
        if not img_dir.exists():
            logger.warning("Subset directory not found: %s — skipping", img_dir)
            continue
        m = evaluate_subset(
            best_pt, DATA_ROOT, subset,
            imgsz=640, batch=16, device="0", conf=0.001, iou=0.6,
        )
        m["experiment"] = best_pt.parent.parent.name  # store exp name
        all_metrics.append(m)
    return all_metrics


def _get_params_flops(best_pt: Path) -> tuple[float, float]:
    """Extract model params (M) and FLOPs (G) from checkpoint."""
    import torch
    from ultralytics.utils.torch_utils import model_info

    ckpt = torch.load(str(best_pt), map_location="cpu", weights_only=False)
    model = ckpt.get("model") or ckpt.get("ema")
    if model is None:
        return 0.0, 0.0
    info = model_info(model, imgsz=640, verbose=False)
    params_m = info.get("parameters", 0) / 1e6
    flops_g = info.get("GFLOPs", 0)
    return round(params_m, 1), round(flops_g, 1)


def build_ablation_table(
    experiments: list[dict],
    all_metrics: dict[str, list[dict]],
) -> Table:
    """Build a rich Table for the ablation comparison."""
    console = Console()
    table = Table(
        title="Ablation Experiment Comparison",
        title_style="bold cyan",
        caption=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    columns = ["Subset"]
    for exp in experiments:
        columns.append(f"{exp['label']}\nBox mAP50")
        columns.append(f"{exp['label']}\nDice")
    table.add_column("Subset", style="dim")
    for col in columns[1:]:
        table.add_column(col, justify="right")

    for subset in SUBSETS:
        row = [subset]
        for exp in experiments:
            label = exp["label"]
            subset_metrics = all_metrics.get(label, [])
            m = next((s for s in subset_metrics if s["subset"] == subset), None)
            if m:
                row.append(f"{m['box_map50']:.4f}")
                row.append(f"{m['dice']:.4f}")
            else:
                row.append("—")
                row.append("—")
        table.add_row(*row)

    # Mean row
    row = ["**Mean**"]
    for exp in experiments:
        label = exp["label"]
        subset_metrics = all_metrics.get(label, [])
        if subset_metrics:
            avg_box = sum(m["box_map50"] for m in subset_metrics) / len(subset_metrics)
            avg_dice = sum(m["dice"] for m in subset_metrics) / len(subset_metrics)
            row.append(f"{avg_box:.4f}")
            row.append(f"{avg_dice:.4f}")
        else:
            row.append("—")
            row.append("—")
    table.add_row(*row, style="bold")
    return table


def build_improvement_table(
    experiments: list[dict],
    all_metrics: dict[str, list[dict]],
) -> Table:
    """Build a rich Table showing improvements over baseline."""
    console = Console()
    table = Table(
        title="Improvements over Baseline (Δ Dice)",
        title_style="bold green",
    )

    table.add_column("Subset", style="dim")
    baseline_label = experiments[0]["label"]
    for exp in experiments[1:]:
        table.add_column(f"{exp['label']}\nΔ Dice", justify="right")
        table.add_column(f"{exp['label']}\nΔ %", justify="right")

    baseline_metrics = all_metrics.get(baseline_label, [])

    for subset in SUBSETS:
        row = [subset]
        base = next((m for m in baseline_metrics if m["subset"] == subset), None)
        base_dice = base["dice"] if base else 0.0

        for exp in experiments[1:]:
            exp_metrics = all_metrics.get(exp["label"], [])
            em = next((m for m in exp_metrics if m["subset"] == subset), None)
            if em and base:
                delta = em["dice"] - base_dice
                delta_pct = (delta / base_dice * 100) if base_dice > 0 else 0.0
                row.append(f"{delta:+.4f}")
                row.append(f"{delta_pct:+.1f}%")
            else:
                row.append("—")
                row.append("—")
        table.add_row(*row)

    # Mean improvement
    row = ["**Mean**"]
    for exp in experiments[1:]:
        exp_metrics = all_metrics.get(exp["label"], [])
        if exp_metrics and baseline_metrics:
            deltas = []
            for subset in SUBSETS:
                base = next((m for m in baseline_metrics if m["subset"] == subset), None)
                em = next((m for m in exp_metrics if m["subset"] == subset), None)
                if em and base:
                    deltas.append(em["dice"] - base["dice"])
            if deltas:
                avg_delta = sum(deltas) / len(deltas)
                base_mean_dice = sum(m["dice"] for m in baseline_metrics) / len(baseline_metrics)
                avg_pct = avg_delta / base_mean_dice * 100 if base_mean_dice > 0 else 0.0
                row.append(f"{avg_delta:+.4f}")
                row.append(f"{avg_pct:+.1f}%")
            else:
                row.append("—")
                row.append("—")
        else:
            row.append("—")
            row.append("—")
    table.add_row(*row, style="bold")
    return table


def write_reports(
    experiments: list[dict],
    all_metrics: dict[str, list[dict]],
    output_dir: Path,
) -> None:
    """Write ablation_table.md and ablation_table.csv."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Compute per-experiment means
    exp_means: dict[str, dict] = {}
    for exp in experiments:
        label = exp["label"]
        mets = all_metrics.get(label, [])
        if not mets:
            continue
        means = {"Label": label}
        for key in ["box_map50", "box_map", "seg_map50", "seg_map",
                     "seg_p", "seg_r", "dice", "miou", "fps"]:
            vals = [m[key] for m in mets if key in m]
            means[key] = round(sum(vals) / len(vals), 4) if vals else 0.0
        params, flops = _get_params_flops(experiments[0]["best_pt"])
        means["params_m"] = params
        means["flops_g"] = flops
        exp_means[label] = means

    # --- CSV ---
    csv_headers = ["Subset"]
    for exp in experiments:
        csv_headers += [
            f"{exp['label']}_Box_mAP50",
            f"{exp['label']}_Dice",
        ]

    csv_lines = [",".join(csv_headers)]
    for subset in SUBSETS:
        row = [subset]
        for exp in experiments:
            label = exp["label"]
            mets = all_metrics.get(label, [])
            m = next((s for s in mets if s["subset"] == subset), None)
            row.append(str(m["box_map50"]) if m else "")
            row.append(str(m["dice"]) if m else "")
        csv_lines.append(",".join(row))

    # Means row
    row = ["Mean"]
    for exp in experiments:
        label = exp["label"]
        means = exp_means.get(label, {})
        row.append(str(means.get("box_map50", "")))
        row.append(str(means.get("dice", "")))
    csv_lines.append(",".join(row))

    # Summary rows
    csv_lines.append("")
    csv_lines.append("Summary")
    csv_lines.append("Label,Box_mAP50,Dice,mIoU,FPS,Params_M,FLOPs_G")
    for exp in experiments:
        label = exp["label"]
        means = exp_means.get(label, {})
        csv_lines.append(
            f"{label},{means.get('box_map50','')},{means.get('dice','')},"
            f"{means.get('miou','')},{means.get('fps','')},"
            f"{means.get('params_m','')},{means.get('flops_g','')}"
        )

    (output_dir / "ablation_table.csv").write_text("\n".join(csv_lines), encoding="utf-8")

    # --- Markdown ---
    md_lines = [
        "# Ablation Experiment Results",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Per-Subset Comparison",
        "",
    ]

    # Header
    md_lines.append("| Subset | " + " | ".join(
        f"{exp['label']} Box mAP50" for exp in experiments
    ) + " | " + " | ".join(
        f"{exp['label']} Dice" for exp in experiments
    ) + " |")
    md_lines.append("|--------|" + "|".join(
        ["--------|" for _ in range(len(experiments) * 2)]
    ))

    for subset in SUBSETS:
        cols = [subset]
        for exp in experiments:
            mets = all_metrics.get(exp["label"], [])
            m = next((s for s in mets if s["subset"] == subset), None)
            cols.append(f"{m['box_map50']:.4f}" if m else "—")
        for exp in experiments:
            mets = all_metrics.get(exp["label"], [])
            m = next((s for s in mets if s["subset"] == subset), None)
            cols.append(f"{m['dice']:.4f}" if m else "—")
        md_lines.append("| " + " | ".join(cols) + " |")

    # Mean row
    mean_cols = ["**Mean**"]
    for exp in experiments:
        label = exp["label"]
        means = exp_means.get(label, {})
        mean_cols.append(f"{means.get('box_map50', 0):.4f}")
    for exp in experiments:
        label = exp["label"]
        means = exp_means.get(label, {})
        mean_cols.append(f"{means.get('dice', 0):.4f}")
    md_lines.append("| " + " | ".join(mean_cols) + " |")

    # Summary table
    md_lines += [
        "",
        "## Summary",
        "",
        "| Experiment | Box mAP50 | Dice | mIoU | FPS | Params (M) | FLOPs (G) |",
        "|------------|-----------|------|------|-----|------------|-----------|",
    ]
    baseline_mean = exp_means.get(experiments[0]["label"], {})
    for exp in experiments:
        label = exp["label"]
        means = exp_means.get(label, {})
        delta_dice = ""
        if label != experiments[0]["label"] and "dice" in means and "dice" in baseline_mean:
            d = means["dice"] - baseline_mean["dice"]
            delta_dice = f" (+{d:+.4f})" if d >= 0 else f" ({d:+.4f})"
        md_lines.append(
            f"| {label} | {means.get('box_map50',0):.4f} | "
            f"{means.get('dice',0):.4f}{delta_dice} | {means.get('miou',0):.4f} | "
            f"{means.get('fps',0):.1f} | {means.get('params_m',0):.1f} | "
            f"{means.get('flops_g',0):.1f} |"
        )

    (output_dir / "ablation_table.md").write_text("\n".join(md_lines), encoding="utf-8")


def plot_ablation_chart(
    experiments: list[dict],
    all_metrics: dict[str, list[dict]],
    output_dir: Path,
) -> None:
    """Generate a grouped bar chart comparing Dice scores across subsets."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [exp["label"] for exp in experiments]
    x = np.arange(len(SUBSETS))
    width = 0.8 / len(experiments)

    fig, ax = plt.subplots(figsize=(14, 6))

    colors = ["#2c3e50", "#e74c3c", "#2ecc71", "#3498db"]
    for i, exp in enumerate(experiments):
        mets = all_metrics.get(exp["label"], [])
        dice_vals = []
        for subset in SUBSETS:
            m = next((s for s in mets if s["subset"] == subset), None)
            dice_vals.append(m["dice"] if m else 0.0)

        offset = (i - len(experiments) / 2 + 0.5) * width
        bars = ax.bar(x + offset, dice_vals, width, label=exp["label"],
                      color=colors[i % len(colors)], edgecolor="white", linewidth=0.5)

        for bar, val in zip(bars, dice_vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{val:.3f}", ha="center", va="bottom", fontsize=7)

    # Baseline reference line
    baseline_mets = all_metrics.get(labels[0], [])
    if baseline_mets:
        baseline_mean = sum(m["dice"] for m in baseline_mets) / len(baseline_mets)
        ax.axhline(y=baseline_mean, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
        ax.text(len(SUBSETS) - 0.5, baseline_mean + 0.01, f"Baseline mean: {baseline_mean:.3f}",
                fontsize=8, color="gray", ha="right")

    ax.set_xlabel("Test Subset")
    ax.set_ylabel("Dice Score")
    ax.set_title("Ablation Study: Dice Score by Subset", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(SUBSETS)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    chart_path = output_dir / "ablation_chart.png"
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    logger.info("Chart saved to %s", chart_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare ablation experiment results"
    )
    parser.add_argument("--runs", nargs="+", required=True,
                        help="Experiment labels as label:run_dir pairs "
                             "(e.g. baseline:yolo11s_seg_v1 p2:exp2_p2)")
    parser.add_argument("--eval-only", action="store_true", default=False,
                        help="Re-evaluate using eval_per_subset (default: True)")
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "results",
                        help="Output directory for reports")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Parse experiment specs
    experiments: list[dict] = []
    for spec in args.runs:
        if ":" in spec:
            label, run_dir = spec.split(":", 1)
        else:
            label = run_dir = spec
        best_pt = _find_best_pt(run_dir)
        experiments.append({"label": label, "run_dir": run_dir, "best_pt": best_pt})
        logger.info("Experiment '%s' → %s", label, best_pt)

    if not experiments:
        logger.error("No experiments specified")
        sys.exit(1)

    # Evaluate each experiment on all subsets
    all_metrics: dict[str, list[dict]] = {}
    for exp in experiments:
        logger.info("=== Evaluating %s ===", exp["label"])
        mets = evaluate_single(exp["best_pt"])
        all_metrics[exp["label"]] = mets

    # Display tables
    console = Console()
    console.print(build_ablation_table(experiments, all_metrics))
    console.print()
    console.print(build_improvement_table(experiments, all_metrics))

    # Write reports
    write_reports(experiments, all_metrics, args.output_dir)
    plot_ablation_chart(experiments, all_metrics, args.output_dir)

    logger.info("Reports written to %s", args.output_dir)


if __name__ == "__main__":
    main()
