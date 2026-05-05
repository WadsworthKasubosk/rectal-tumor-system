"""Figure 5-2: ΔDice heatmap — per-model Dice change vs Baseline across 5 test subsets."""
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
from pathlib import Path

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# ── Data: Dice scores from ablation_summary.csv ──────────────────────────
subsets = ['CVC-300', 'CVC-ClinicDB', 'CVC-ColonDB', 'ETIS-LaribPolypDB', 'Kvasir']
model_names = ['+P2', '+CBAM', '+P2+CBAM']

baseline_dice =  [0.5172, 0.8450, 0.6262, 0.3541, 0.8142]
p2_dice =         [0.5474, 0.7960, 0.5616, 0.2905, 0.7732]
cbam_dice =       [0.6306, 0.7296, 0.5965, 0.2520, 0.7597]
p2_cbam_dice =    [0.5757, 0.7564, 0.5940, 0.3409, 0.7860]

# ── Compute ΔDice ────────────────────────────────────────────────────────
all_dice = np.array([p2_dice, cbam_dice, p2_cbam_dice])
delta = all_dice - np.array(baseline_dice)

# ── Plot ──────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.5, 3.2))

cmap = plt.cm.RdYlGn
norm = matplotlib.colors.TwoSlopeNorm(vcenter=0, vmin=-0.12, vmax=0.12)

im = ax.imshow(delta, cmap=cmap, norm=norm, aspect='auto')

# Annotate each cell
for i in range(len(model_names)):
    for j in range(len(subsets)):
        val = delta[i, j]
        text = f'{val:+.4f}'
        color = 'white' if abs(val) > 0.06 else 'black'
        ax.text(j, i, text, ha='center', va='center', fontsize=10, fontweight='bold', color=color)

ax.set_xticks(range(len(subsets)))
ax.set_xticklabels(subsets, fontsize=10)
ax.set_yticks(range(len(model_names)))
ax.set_yticklabels(model_names, fontsize=10)

# Colorbar
cbar = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label('ΔDice vs Baseline', fontsize=10)

ax.set_title('Figure 5-2: Per-Subset ΔDice vs Baseline (YOLO11s-seg Ablation)', fontsize=12, fontweight='bold', pad=12)

plt.tight_layout()

out = Path(__file__).resolve().parent / 'fig5-2_delta_dice_heatmap.png'
fig.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
out_svg = out.with_suffix('.svg')
fig.savefig(out_svg, bbox_inches='tight', facecolor='white')
print(f'Saved → {out}')
print(f'Saved → {out_svg}')
plt.close()
