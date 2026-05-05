"""Convert image+mask pairs from raw datasets to YOLOv11-seg label format.

Each mask is processed with contour extraction, polygon simplification, and
noise filtering.  Output txt files contain normalized polygon coordinates.
"""

import argparse
import logging
from pathlib import Path

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "datasets" / "raw"
OUT_DIR = PROJECT_ROOT / "datasets" / "rectal_tumor"


def find_image_mask_pairs(raw_dir: Path) -> list[tuple[Path, Path]]:
    """Scan raw_dir for image/mask file pairs.

    Returns list of (image_path, mask_path) tuples.
    """
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    pairs: list[tuple[Path, Path]] = []

    for img_path in sorted(raw_dir.rglob("*")):
        if img_path.suffix.lower() not in image_exts:
            continue
        parent = img_path.parent

        # Skip files that are clearly masks (in mask directories)
        if parent.name.lower() in {"masks", "ground truth", "ground_truth", "mask"}:
            continue

        dataset_root = parent.parent  # grandparent of files in Original/, etc.

        # Common mask naming conventions — ordered by specificity
        for mask_candidate in [
            # Sibling dir "Ground Truth" / same filename (CVC-ClinicDB pattern)
            dataset_root / "Ground Truth" / img_path.name,
            dataset_root / "Ground Truth" / f"{img_path.stem}.png",
            dataset_root / "Ground Truth" / f"{img_path.stem}.jpg",
            dataset_root / "ground_truth" / img_path.name,
            dataset_root / "ground_truth" / f"{img_path.stem}.png",
            # Sibling dir "masks" / same or similar filename (Kvasir-SEG pattern)
            dataset_root / "masks" / img_path.name,
            dataset_root / "masks" / f"{img_path.stem}.png",
            dataset_root / "masks" / f"{img_path.stem}.jpg",
            dataset_root / "masks" / f"{img_path.stem}{img_path.suffix}",
            # Child dir "Ground Truth" (alternative)
            parent / "Ground Truth" / img_path.name,
            parent / "Ground Truth" / f"{img_path.stem}.png",
            parent / "masks" / img_path.name,
            parent / "masks" / f"{img_path.stem}.png",
            # Same folder with _mask suffix
            parent / f"{img_path.stem}_mask{img_path.suffix}",
            parent / f"{img_path.stem}_mask.png",
            parent / f"{img_path.stem}_mask.jpg",
        ]:
            if mask_candidate.exists():
                pairs.append((img_path, mask_candidate))
                break

    return pairs


def extract_polygons_from_mask(
    mask_path: Path,
    img_shape: tuple[int, int],
    epsilon_factor: float = 0.001,
    min_area_ratio: float = 0.0005,
) -> list[list[tuple[float, float]]]:
    """Extract normalized YOLO-seg polygons from a binary mask.

    Args:
        mask_path: Path to mask image.
        img_shape: (height, width) of the corresponding image.
        epsilon_factor: Fraction of perimeter for approxPolyDP.
        min_area_ratio: Minimum contour area relative to image area.

    Returns:
        List of polygons, each as list of (x, y) normalized to [0,1].
    """
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        logger.warning("Cannot read mask: %s", mask_path)
        return []

    h, w = img_shape
    img_area = h * w
    min_area = img_area * min_area_ratio

    # Resize mask to match image dimensions if needed
    if mask.shape[:2] != (h, w):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

    # Binarize
    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS
    )

    polygons: list[list[tuple[float, float]]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        perimeter = cv2.arcLength(cnt, closed=True)
        epsilon = epsilon_factor * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, closed=True)

        vertices = approx.squeeze(axis=1)
        if vertices.ndim != 2 or len(vertices) < 3:
            continue

        normalized: list[tuple[float, float]] = []
        for pt in vertices:
            nx = round(float(pt[0]) / w, 6)
            ny = round(float(pt[1]) / h, 6)
            nx = max(0.0, min(1.0, nx))
            ny = max(0.0, min(1.0, ny))
            normalized.append((nx, ny))

        polygons.append(normalized)

    return polygons


def polygons_to_yolo_line(polygons: list[list[tuple[float, float]]]) -> list[str]:
    """Convert polygons to YOLO-seg text lines (class 0 = tumor)."""
    lines: list[str] = []
    for poly in polygons:
        coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in poly)
        lines.append(f"0 {coords}")
    return lines


def convert_dataset(raw_dir: Path, out_dir: Path) -> dict:
    """Main conversion routine.

    Returns statistics dict.
    """
    pairs = find_image_mask_pairs(raw_dir)
    logger.info("Found %d image-mask pairs in %s", len(pairs), raw_dir)

    if not pairs:
        logger.warning("No pairs found – check raw directory structure and naming conventions.")
        return {"total_images": 0, "valid_labels": 0, "total_polygons": 0}

    out_images = out_dir / "images" / "train"
    out_labels = out_dir / "labels" / "train"
    out_images.mkdir(parents=True, exist_ok=True)
    out_labels.mkdir(parents=True, exist_ok=True)

    total_images = 0
    total_polygons = 0
    valid_labels = 0

    for img_path, mask_path in pairs:
        img = cv2.imread(str(img_path))
        if img is None:
            logger.warning("Cannot read image: %s", img_path)
            continue

        h, w = img.shape[:2]
        polygons = extract_polygons_from_mask(mask_path, (h, w))

        total_images += 1
        if polygons:
            valid_labels += 1
            total_polygons += len(polygons)

        # Copy image
        out_img = out_images / img_path.name
        cv2.imwrite(str(out_img), img)

        # Write label
        out_label = out_labels / f"{img_path.stem}.txt"
        lines = polygons_to_yolo_line(polygons)
        out_label.write_text("\n".join(lines) if lines else "", encoding="utf-8")

    stats = {
        "total_images": total_images,
        "valid_labels": valid_labels,
        "total_polygons": total_polygons,
    }
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert image+mask datasets to YOLOv11-seg format"
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR,
                        help="Path to raw datasets directory")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR,
                        help="Path to output YOLO dataset directory")
    parser.add_argument("--dataset", type=str, default=None,
                        help="Process a specific raw sub-directory (e.g. Kvasir-SEG)")
    args = parser.parse_args()

    if args.dataset:
        raw_path = args.raw_dir / args.dataset
        if not raw_path.exists():
            logger.error("Dataset directory not found: %s", raw_path)
            return
        stats = convert_dataset(raw_path, args.out_dir)
    else:
        # Process all subdirectories in raw/
        all_stats = {"total_images": 0, "valid_labels": 0, "total_polygons": 0}
        for subdir in sorted(args.raw_dir.iterdir()):
            if subdir.is_dir():
                logger.info("Processing: %s", subdir.name)
                stats = convert_dataset(subdir, args.out_dir)
                for k in all_stats:
                    all_stats[k] += stats[k]
        stats = all_stats

    logger.info("=== Conversion Summary ===")
    logger.info("Total images:      %d", stats["total_images"])
    logger.info("Valid labels:      %d", stats["valid_labels"])
    logger.info("Total polygons:    %d", stats["total_polygons"])
    if stats["valid_labels"] > 0:
        logger.info("Avg polygons/img:  %.2f", stats["total_polygons"] / stats["valid_labels"])


if __name__ == "__main__":
    main()
