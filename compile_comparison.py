"""Compile the 4-model ablation comparison table for thesis chapter 4."""
import csv
from pathlib import Path

RESULTS = {
    "baseline":     "results/baseline_eval/per_subset_metrics.csv",
    "exp2_p2":      "results/exp2_eval/per_subset_metrics.csv",
    "exp3_cbam":    "results/exp3_eval/per_subset_metrics.csv",
    "exp4_p2_cbam": "results/exp4_eval/per_subset_metrics.csv",
}

MODEL_INFO = {
    "baseline":     {"label": "Baseline (YOLO11s-seg)", "params": "10.1M", "flops": "35.3G"},
    "exp2_p2":      {"label": "+P2 Enhancement",        "params": "10.2M", "flops": "38.5G"},
    "exp3_cbam":    {"label": "+CBAM Attention",         "params": "10.5M", "flops": "37.2G"},
    "exp4_p2_cbam": {"label": "+P2 + CBAM (Best)",       "params": "10.6M", "flops": "40.4G"},
}

SUBSETS = ["CVC-300", "CVC-ClinicDB", "CVC-ColonDB", "ETIS-LaribPolypDB", "Kvasir"]

def load_csv(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    by_subset = {}
    for r in rows:
        if r["Subset"] != "Mean":
            by_subset[r["Subset"]] = r
    mean_row = [r for r in rows if r["Subset"] == "Mean"]
    return by_subset, mean_row[0] if mean_row else None

print("# Ablation Study: Per-Subset Comparison\n")
print("## Model Overview\n")
print("| Model | Params | FLOPs | Description |")
print("|---|---|---|---|")
for key, info in MODEL_INFO.items():
    print(f"| {info['label']} | {info['params']} | {info['flops']} | {key} |")

print("\n## Per-Subset Dice Score\n")
header = "| Subset | " + " | ".join(MODEL_INFO[m]["label"] for m in RESULTS) + " |"
print(header)
print("|" + "---|" * (len(RESULTS) + 1))

for subset in SUBSETS:
    row = f"| {subset} |"
    for model_key in RESULTS:
        path = RESULTS[model_key]
        if Path(path).exists():
            by_subset, _ = load_csv(path)
            if subset in by_subset:
                dice = float(by_subset[subset]["Dice"])
                row += f" {dice:.4f} |"
            else:
                row += " ? |"
        else:
            row += " — |"
    print(row)

# Mean row
row = "| **Mean** |"
for model_key in RESULTS:
    path = RESULTS[model_key]
    if Path(path).exists():
        _, mean = load_csv(path)
        if mean:
            dice = float(mean["Dice"])
            row += f" **{dice:.4f}** |"
        else:
            row += " ? |"
    else:
        row += " — |"
print(row)

print("\n## Per-Subset mIoU\n")
print(header.replace("Dice", "mIoU"))
print("|" + "---|" * (len(RESULTS) + 1))
for subset in SUBSETS:
    row = f"| {subset} |"
    for model_key in RESULTS:
        path = RESULTS[model_key]
        if Path(path).exists():
            by_subset, _ = load_csv(path)
            if subset in by_subset:
                miou = float(by_subset[subset]["mIoU"])
                row += f" {miou:.4f} |"
            else:
                row += " ? |"
        else:
            row += " — |"
    print(row)

row = "| **Mean** |"
for model_key in RESULTS:
    path = RESULTS[model_key]
    if Path(path).exists():
        _, mean = load_csv(path)
        if mean:
            miou = float(mean["mIoU"])
            row += f" **{miou:.4f}** |"
        else:
            row += " ? |"
    else:
        row += " — |"
print(row)

print("\n## Mask mAP50 Comparison\n")
print(header.replace("Dice Score", "Mask mAP50"))
print("|" + "---|" * (len(RESULTS) + 1))
for subset in SUBSETS:
    row = f"| {subset} |"
    for model_key in RESULTS:
        path = RESULTS[model_key]
        if Path(path).exists():
            by_subset, _ = load_csv(path)
            if subset in by_subset:
                m = float(by_subset[subset]["Mask_mAP50"])
                row += f" {m:.4f} |"
            else:
                row += " ? |"
        else:
            row += " — |"
    print(row)

row = "| **Mean** |"
for model_key in RESULTS:
    path = RESULTS[model_key]
    if Path(path).exists():
        _, mean = load_csv(path)
        if mean:
            m = float(mean["Mask_mAP50"])
            row += f" **{m:.4f}** |"
        else:
            row += " ? |"
    else:
        row += " — |"
print(row)

print(f"\n> Generated from CPU evaluation. Baseline cloud CUDA Mean Dice: 0.6324")
