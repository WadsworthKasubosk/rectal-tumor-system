#!/bin/bash
# Phase 3: YOLO11s-seg improvement experiments with ablation study
# Run all 3 experiments and generate comparison reports.
set -e
cd "$(dirname "$0")"

PROJECT_ROOT="$(pwd)"

echo "============================================"
echo "  Phase 3: YOLO11s-seg Ablation Experiments"
echo "============================================"
echo ""

echo "=== Experiment 2: +P2 detection head ==="
python train/train_improved.py \
    --model-cfg configs/yolo11s-seg-p2.yaml \
    --epochs 100 --batch 32 --device 0 \
    --name exp2_p2

echo ""
echo "=== Experiment 3: +CBAM attention ==="
python train/train_improved.py \
    --model-cfg configs/yolo11s-seg-cbam.yaml \
    --epochs 100 --batch 32 --device 0 \
    --name exp3_cbam

echo ""
echo "=== Experiment 4: +P2 + CBAM ==="
python train/train_improved.py \
    --model-cfg configs/yolo11s-seg-p2-cbam.yaml \
    --epochs 100 --batch 32 --device 0 \
    --name exp4_p2_cbam

echo ""
echo "=== Ablation Summary ==="
python eval/compare_ablation.py \
    --runs baseline:yolo11s_seg_v1 p2:exp2_p2 cbam:exp3_cbam p2_cbam:exp4_p2_cbam

echo ""
echo "=== Phase 3 complete ==="
echo "Reports: results/ablation_table.md, results/ablation_table.csv, results/ablation_chart.png"
