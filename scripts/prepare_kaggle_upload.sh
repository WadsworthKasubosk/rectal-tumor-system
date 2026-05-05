#!/usr/bin/env bash
# ==============================================================================
# Prepare Kaggle upload packages (cross-platform: uses Python's zipfile)
#
# Produces two zip files in the project root:
#   1. rectal_tumor_dataset.zip — YOLO-formatted dataset
#   2. rectal_tumor_code.zip    — training pipeline code
#
# Usage:  bash scripts/prepare_kaggle_upload.sh
# ==============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Packaging rectal_tumor_dataset.zip ==="

python -c "
import zipfile, os
from pathlib import Path

root = Path('datasets/rectal_tumor')
with zipfile.ZipFile('rectal_tumor_dataset.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(root.rglob('*')):
        if f.is_file():
            zf.write(str(f), str(f))
size_mb = Path('rectal_tumor_dataset.zip').stat().st_size / 1e6
print(f'  Added {len(zf.namelist())} files ({size_mb:.1f} MB)')
"

echo "  Done: rectal_tumor_dataset.zip"

echo ""
echo "=== Packaging rectal_tumor_code.zip ==="

python -c "
import zipfile, os
from pathlib import Path

EXCLUDE_DIRS  = {'__pycache__', '.git', 'runs', 'logs', 'results', 'datasets', '.ipynb_checkpoints'}
EXCLUDE_EXTS  = {'.pyc', '.pyo', '.zip'}
EXCLUDE_NAMES = {'.gitignore', '.DS_Store', 'Thumbs.db'}

INCLUDE = [
    'train', 'eval', 'scripts', 'configs', 'notebooks',
    'run_all.py', 'requirements.txt',
]

with zipfile.ZipFile('rectal_tumor_code.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for item in INCLUDE:
        p = Path(item)
        if not p.exists():
            print(f'  WARNING: {item} not found — skipping')
            continue
        if p.is_file():
            zf.write(str(p), str(p))
        else:
            for f in sorted(p.rglob('*')):
                if not f.is_file():
                    continue
                # Skip excluded directories
                if any(d in EXCLUDE_DIRS for d in f.parts):
                    continue
                # Skip excluded extensions
                if f.suffix.lower() in EXCLUDE_EXTS:
                    continue
                # Skip excluded filenames
                if f.name in EXCLUDE_NAMES:
                    continue
                zf.write(str(f), str(f))
    count = len(zf.namelist())
size_mb = Path('rectal_tumor_code.zip').stat().st_size / 1e6
print(f'  Added {count} files ({size_mb:.1f} MB)')
"

echo "  Done: rectal_tumor_code.zip"

echo ""
echo "=== Upload these files to Kaggle ==="
python -c "
import os
for name in ['rectal_tumor_dataset.zip','rectal_tumor_code.zip']:
    size = os.path.getsize(name)
    if size > 1e6:
        print(f'  {name}: {size/1e6:.1f} MB')
    else:
        print(f'  {name}: {size/1e3:.0f} KB')
"
echo ""
echo "  Dataset → New Dataset → 'rectal-tumor-dataset' (attach dataset zip)"
echo "  Code    → New Dataset → 'rectal-tumor-code'    (attach code zip)"
echo ""
echo "  NOTE: If a zip exceeds 500 MB, use the Kaggle API to upload:"
echo "    kaggle datasets create -p . --dir-mode zip"
echo ""
echo "  After uploading, copy the dataset paths (e.g. username/rectal-tumor-dataset)"
echo "  and paste them into notebooks/kaggle_train.ipynb as placeholders."
