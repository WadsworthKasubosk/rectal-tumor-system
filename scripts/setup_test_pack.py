"""Convert PraNet test pack, remove overlaps from training, and place test data.

The PraNet test pack is the community-standard polyp segmentation test set.
It contains 5 sub-datasets with unified images/ + masks/ structure:
CVC-300 (60), CVC-ClinicDB (62), CVC-ColonDB (380), ETIS (196), Kvasir (100).
Total: 798 test images.
"""

import argparse
import logging
import shutil
from pathlib import Path

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "datasets" / "raw"
TEST_PACK_DIR = RAW_DIR / "TestDataset"
YOLO_DIR = PROJECT_ROOT / "datasets" / "rectal_tumor"


def extract_polygons_from_mask(
    mask_path: Path, img_shape: tuple[int, int]
) -> list[list[tuple[float, float]]]:
    """Extract normalized YOLO-seg polygons from a binary mask."""
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return []

    h, w = img_shape
    img_area = h * w
    min_area = img_area * 0.0005

    if mask.shape[:2] != (h, w):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

    polygons: list[list[tuple[float, float]]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        perimeter = cv2.arcLength(cnt, closed=True)
        epsilon = 0.001 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, closed=True)
        vertices = approx.squeeze(axis=1)
        if vertices.ndim != 2 or len(vertices) < 3:
            continue
        normalized = []
        for pt in vertices:
            nx = round(float(pt[0]) / w, 6)
            ny = round(float(pt[1]) / h, 6)
            normalized.append((max(0.0, min(1.0, nx)), max(0.0, min(1.0, ny))))
        polygons.append(normalized)

    return polygons


def convert_test_pack() -> dict:
    """Convert all PraNet test pack sub-datasets to YOLO-seg labels.

    Images and labels are placed in a temp directory.
    Returns {stem: source_dataset_name} mapping.
    """
    temp_dir = PROJECT_ROOT / "datasets" / "_test_temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    (temp_dir / "images").mkdir(parents=True, exist_ok=True)
    (temp_dir / "labels").mkdir(parents=True, exist_ok=True)

    stem_to_source: dict[str, str] = {}
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    total_polygons = 0

    for ds_dir in sorted(TEST_PACK_DIR.iterdir()):
        if not ds_dir.is_dir():
            continue
        ds_name = ds_dir.name
        img_dir = ds_dir / "images"
        mask_dir = ds_dir / "masks"

        if not img_dir.exists() or not mask_dir.exists():
            continue

        images = [f for f in sorted(img_dir.glob("*"))
                  if f.suffix.lower() in valid_exts]
        count = 0

        for img_path in images:
            mask_path = mask_dir / img_path.name
            if not mask_path.exists():
                # Try common alternatives
                for alt in [mask_dir / f"{img_path.stem}.png",
                           mask_dir / f"{img_path.stem}.jpg",
                           mask_dir / f"{img_path.stem}{img_path.suffix}"]:
                    if alt.exists():
                        mask_path = alt
                        break
                else:
                    continue

            img = cv2.imread(str(img_path))
            if img is None:
                continue
            h, w = img.shape[:2]

            polygons = extract_polygons_from_mask(mask_path, (h, w))

            # Prefix filename with source to avoid collisions across sub-datasets
            out_stem = f"{ds_name}_{img_path.stem}"
            stem_to_source[out_stem] = ds_name

            # Copy image
            out_img = temp_dir / "images" / f"{out_stem}{img_path.suffix}"
            cv2.imwrite(str(out_img), img)

            # Write label
            out_label = temp_dir / "labels" / f"{out_stem}.txt"
            lines = []
            for poly in polygons:
                coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in poly)
                lines.append(f"0 {coords}")
            out_label.write_text("\n".join(lines) if lines else "", encoding="utf-8")
            total_polygons += len(polygons)
            count += 1

        logger.info("  %s: %d images converted", ds_name, count)

    logger.info("Test pack total: %d images, %d polygons",
                len(stem_to_source), total_polygons)
    return stem_to_source


def remove_overlaps_from_training(stem_to_source: dict[str, str]) -> int:
    """Remove training images that overlap with Kvasir or CVC-ClinicDB test splits.

    Only checks datasets that exist in both training and test (Kvasir, CVC-ClinicDB).
    CVC-300, CVC-ColonDB, ETIS are external-only and never overlap with training.
    Returns number of removed images.
    """
    # Only these two datasets have training data that could overlap
    OVERLAP_SOURCES = {"Kvasir", "CVC-ClinicDB"}

    # Build set of original stems for overlapping datasets only
    original_test_stems: set[str] = set()
    for stem, source in stem_to_source.items():
        if source in OVERLAP_SOURCES:
            # Stems are like "Kvasir_cju0..." -> original is after first "_"
            parts = stem.split("_", 1)
            if len(parts) == 2:
                original_test_stems.add(parts[1])

    logger.info("Checking overlaps for %d test stems from Kvasir + CVC-ClinicDB",
                len(original_test_stems))

    removed = 0
    for split_name in ["train", "val"]:
        img_dir = YOLO_DIR / "images" / split_name
        lbl_dir = YOLO_DIR / "labels" / split_name
        if not img_dir.exists():
            continue

        for img_path in list(img_dir.glob("*")):
            if not img_path.is_file():
                continue
            if img_path.stem in original_test_stems:
                lbl_path = lbl_dir / f"{img_path.stem}.txt"
                img_path.unlink()
                if lbl_path.exists():
                    lbl_path.unlink()
                removed += 1

    return removed


def place_test_data(stem_to_source: dict[str, str]) -> None:
    """Move converted test data into test/ with source subfolders."""
    temp_dir = PROJECT_ROOT / "datasets" / "_test_temp"
    test_img_root = YOLO_DIR / "images" / "test"
    test_lbl_root = YOLO_DIR / "labels" / "test"

    # Clear existing test content
    for d in [test_img_root, test_lbl_root]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    for stem, source in sorted(stem_to_source.items()):
        # Find files in temp
        for ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
            img_src = temp_dir / "images" / f"{stem}{ext}"
            if img_src.exists():
                break
        else:
            continue

        lbl_src = temp_dir / "labels" / f"{stem}.txt"

        dst_img_dir = test_img_root / source
        dst_lbl_dir = test_lbl_root / source
        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(img_src, dst_img_dir / img_src.name)
        if lbl_src.exists():
            shutil.copy2(lbl_src, dst_lbl_dir / lbl_src.name)

    # Cleanup temp
    shutil.rmtree(temp_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PraNet test pack, remove train overlaps, place test data"
    )
    parser.add_argument("--skip-overlap-check", action="store_true",
                        help="Skip removing overlapping training images")
    args = parser.parse_args()

    logger.info("=== Step 1: Convert PraNet test pack ===")
    stem_to_source = convert_test_pack()

    if not args.skip_overlap_check:
        logger.info("=== Step 2: Remove overlaps from training ===")
        all_stems = set(stem_to_source.keys())
        removed = remove_overlaps_from_training(stem_to_source)
        logger.info("Removed %d overlapping images from train/val", removed)

    logger.info("=== Step 3: Place test data ===")
    place_test_data(stem_to_source)

    # Summary
    logger.info("=== Done ===")
    for split in ["train", "val", "test"]:
        img_dir = YOLO_DIR / "images" / split
        count = 0
        if img_dir.exists():
            count = len(list(img_dir.rglob("*")))
        logger.info("  %s: %d files", split, count)


if __name__ == "__main__":
    main()
