#!/bin/bash
# SMOKE_AND_TRAIN.sh
# Phase 3 server-side script: smoke-test then train all 3 experiments.
# Usage: bash SMOKE_AND_TRAIN.sh
set -e

ROOT=/workspace/project
cd "$ROOT"

echo "============================================"
echo "  Step 1/2: Smoke Test (model build + forward)"
echo "============================================"

python -c "
import torch
from pathlib import Path

import ultralytics.nn.tasks as _tasks
from train.cbam_module import CBAM
_tasks.CBAM = CBAM

from ultralytics import YOLO

x = torch.randn(1, 3, 640, 640).cuda()

tests = [
    ('P2',         'configs/yolo11s-seg-p2.yaml',      34000, 10.2),
    ('CBAM',       'configs/yolo11s-seg-cbam.yaml',      8400, 10.5),
    ('P2+CBAM',    'configs/yolo11s-seg-p2-cbam.yaml',  34000, 10.6),
]

all_ok = True
for label, cfg, exp_anchors, exp_params in tests:
    m = YOLO(str(Path(cfg)), task='segment')
    m.load(str(Path('yolo11s-seg.pt')))
    m.model.eval()
    with torch.no_grad():
        y = m.model(x)
        n = y[0].shape[2]
        p = sum(p.numel() for p in m.model.parameters()) / 1e6
        ok = (n == exp_anchors)
        tag = 'PASS' if ok else 'FAIL'
        if not ok:
            all_ok = False
        print(f'{tag}: {label:10s}  anchors={n:5d} (exp={exp_anchors})  params={p:.1f}M (exp={exp_params:.1f}M)')

if not all_ok:
    print('SMOKE TEST FAILED — aborting')
    exit(1)
print('Smoke test passed!')
"

echo ""
echo "============================================"
echo "  Step 2/2: Phase 3 Training + Ablation"
echo "============================================"

bash run_phase3.sh
