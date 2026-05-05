#!/usr/bin/env bash
# Chain: run exp3 then exp4 after this script is called
set -e
LOGFILE="/tmp/chain_eval.log"
echo "===== $(date) Starting exp3_cbam =====" | tee -a "$LOGFILE"
python eval/eval_per_subset.py --weights backend/weights/exp3_cbam_best.pt --output-dir results/exp3_eval --device cpu >> /tmp/exp3_eval.log 2>&1
echo "===== $(date) Finished exp3_cbam =====" | tee -a "$LOGFILE"
echo "===== $(date) Starting exp4_p2_cbam =====" | tee -a "$LOGFILE"
python eval/eval_per_subset.py --weights backend/weights/improved_best.pt --output-dir results/exp4_eval --device cpu >> /tmp/exp4_eval.log 2>&1
echo "===== $(date) Finished exp4_p2_cbam =====" | tee -a "$LOGFILE"
echo "ALL DONE $(date)" | tee -a "$LOGFILE"
