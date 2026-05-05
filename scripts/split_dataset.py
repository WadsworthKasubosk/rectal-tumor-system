"""Split training-pool datasets into train/val/test (8:1:1) with fixed seed.

External test sets (CVC-ColonDB, ETIS-LaribPolypDB) are placed separately
under test/ with subfolder markers, not mixed with the training pool.

Source directory is images/train (pre-split). Train files stay in place;
val/test files are moved to their respective directories via shutil.move.
"""

import argparse
import logging
import random
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "datasets" / "rectal_tumor"
RANDOM_SEED = 42

EXTERNAL_TEST_MARKERS = {"cvc-colondb", "colondb", "etis", "laribpolypdb", "larib"}


def is_external(filename: str) -> bool:
    """Check if a file belongs to an external test dataset."""
    lower = filename.lower()
    return any(m in lower for m in EXTERNAL_TEST_MARKERS)


def move_file(src: Path, dst: Path) -> None:
    """Move a file, creating parent dirs as needed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


def split_dataset(
    src_images: Path,
    src_labels: Path,
    out_images: Path,
    out_labels: Path,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = RANDOM_SEED,
) -> dict[str, int]:
    """Split train-pool samples using move semantics (train stays in place).

    Returns counts per split.
    """
    out_images_val = out_images / "val"
    out_images_test = out_images / "test"
    out_labels_val = out_labels / "val"
    out_labels_test = out_labels / "test"

    for d in [out_images_val, out_images_test, out_labels_val, out_labels_test]:
        d.mkdir(parents=True, exist_ok=True)

    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    image_files = [f for f in sorted(src_images.glob("*"))
                   if f.is_file() and f.suffix.lower() in valid_exts]

    train_pool: list[Path] = []
    external: list[Path] = []

    for img in image_files:
        if is_external(img.name):
            external.append(img)
        else:
            train_pool.append(img)

    logger.info("Train pool images: %d", len(train_pool))
    logger.info("External test images: %d", len(external))

    # Shuffle and split training pool
    rng = random.Random(seed)
    rng.shuffle(train_pool)

    n = len(train_pool)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    val_files = train_pool[n_train:n_train + n_val]
    test_files = train_pool[n_train + n_val:]

    # Move val files from train/ to val/
    for img in val_files:
        move_file(img, out_images_val / img.name)
        lbl = src_labels / f"{img.stem}.txt"
        if lbl.exists():
            move_file(lbl, out_labels_val / lbl.name)

    # Move test (from pool) files from train/ to test/
    for img in test_files:
        move_file(img, out_images_test / img.name)
        lbl = src_labels / f"{img.stem}.txt"
        if lbl.exists():
            move_file(lbl, out_labels_test / lbl.name)

    # External test files: move to test/ with source subfolder
    for img in external:
        source_folder = "CVC-ColonDB" if "colondb" in img.name.lower() else "ETIS-LaribPolypDB"

        ext_img_dir = out_images_test / source_folder
        ext_lbl_dir = out_labels_test / source_folder
        ext_img_dir.mkdir(parents=True, exist_ok=True)
        ext_lbl_dir.mkdir(parents=True, exist_ok=True)

        move_file(img, ext_img_dir / img.name)
        lbl = src_labels / f"{img.stem}.txt"
        if lbl.exists():
            move_file(lbl, ext_lbl_dir / lbl.name)
        else:
            (ext_lbl_dir / f"{img.stem}.txt").write_text("", encoding="utf-8")

    counts = {
        "train_pool_total": len(train_pool),
        "train": n_train,
        "val": n_val,
        "test_from_pool": len(test_files),
        "external_test": len(external),
        "test_total": len(test_files) + len(external),
    }
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split training-pool datasets 8:1:1, external sets -> test/"
    )
    parser.add_argument("--src-images", type=Path,
                        default=DATASET_DIR / "images" / "train",
                        help="Source images directory (pre-split, also train target)")
    parser.add_argument("--src-labels", type=Path,
                        default=DATASET_DIR / "labels" / "train",
                        help="Source labels directory (pre-split, also train target)")
    parser.add_argument("--out-images", type=Path,
                        default=DATASET_DIR / "images",
                        help="Output images root")
    parser.add_argument("--out-labels", type=Path,
                        default=DATASET_DIR / "labels",
                        help="Output labels root")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED,
                        help="Random seed for reproducible splits")
    args = parser.parse_args()

    # Clean only val and test targets (train is both source and target)
    for parent in [args.out_images, args.out_labels]:
        for sub in ["val", "test"]:
            d = parent / sub
            if d.exists():
                shutil.rmtree(d)

    counts = split_dataset(
        args.src_images,
        args.src_labels,
        args.out_images,
        args.out_labels,
        seed=args.seed,
    )

    logger.info("=== Split Summary (seed=%d) ===", args.seed)
    logger.info("Train pool total:   %d", counts["train_pool_total"])
    logger.info("  -> Train:          %d (%.0f%%)", counts["train"],
                counts["train"] / max(counts["train_pool_total"], 1) * 100)
    logger.info("  -> Val:            %d (%.0f%%)", counts["val"],
                counts["val"] / max(counts["train_pool_total"], 1) * 100)
    logger.info("  -> Test (pool):    %d (%.0f%%)", counts["test_from_pool"],
                counts["test_from_pool"] / max(counts["train_pool_total"], 1) * 100)
    logger.info("External test sets: %d", counts["external_test"])
    logger.info("Test total:         %d", counts["test_total"])


if __name__ == "__main__":
    main()
