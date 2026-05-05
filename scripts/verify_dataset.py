"""Verify dataset integrity and generate preview images with YOLO-seg overlay."""

import argparse
import logging
import random
from pathlib import Path

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "datasets" / "rectal_tumor"
PREVIEW_DIR = PROJECT_ROOT / "datasets" / "preview"
CLASS_NAMES = {0: "tumor"}


def count_samples(images_dir: Path, labels_dir: Path) -> dict[str, int]:
    """Count image and label files in a split directory (recursive for test/)."""
    valids = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    images = [f for f in sorted(images_dir.rglob("*"))
              if f.is_file() and f.suffix.lower() in valids]
    labels = [f for f in sorted(labels_dir.rglob("*.txt")) if f.is_file()]

    non_empty_labels = sum(1 for l in labels if l.stat().st_size > 0)
    return {
        "images": len(images),
        "labels": len(labels),
        "non_empty_labels": non_empty_labels,
    }


def parse_yolo_label(label_path: Path) -> list[list[tuple[float, float]]]:
    """Parse a YOLO-seg label file into list of polygons."""
    polygons: list[list[tuple[float, float]]] = []
    if not label_path.exists() or label_path.stat().st_size == 0:
        return polygons

    for line in label_path.read_text(encoding="utf-8").strip().splitlines():
        parts = line.strip().split()
        if len(parts) < 7:  # class + at least 3 points (6 coords)
            continue
        # Skip class ID (parts[0])
        coords = [float(x) for x in parts[1:]]
        pts = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
        polygons.append(pts)
    return polygons


def draw_polygons_on_image(
    img: np.ndarray,
    polygons: list[list[tuple[float, float]]],
    color: tuple[int, int, int] = (0, 255, 0),
) -> np.ndarray:
    """Draw YOLO-seg polygons onto an image (in-place)."""
    h, w = img.shape[:2]
    for poly in polygons:
        pts = np.array([(int(x * w), int(y * h)) for x, y in poly], dtype=np.int32)
        cv2.polylines(img, [pts], isClosed=True, color=color, thickness=2)
    return img


def generate_previews(
    images_dir: Path,
    labels_dir: Path,
    preview_dir: Path,
    num_samples: int = 5,
    split_name: str = "",
) -> list[Path]:
    """Randomly select images and save overlay previews. Returns list of saved paths."""
    valids = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    images = [f for f in sorted(images_dir.rglob("*"))
              if f.is_file() and f.suffix.lower() in valids]

    sample = random.sample(images, min(num_samples, len(images)))

    preview_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    for img_path in sample:
        # Handle nested subdirectories (e.g. test/CVC-300/img.png)
        rel = img_path.relative_to(images_dir)
        label_path = labels_dir / rel.parent / f"{img_path.stem}.txt"
        if not label_path.exists():
            label_path = labels_dir / f"{img_path.stem}.txt"
        polygons = parse_yolo_label(label_path)

        img = cv2.imread(str(img_path))
        if img is None:
            continue

        draw_polygons_on_image(img, polygons)

        out_name = f"{split_name}_{img_path.name}" if split_name else img_path.name
        out_path = preview_dir / out_name
        cv2.imwrite(str(out_path), img)
        saved.append(out_path)
        logger.info("  Preview saved: %s (%d polygons)", out_path.name, len(polygons))

    return saved


def verify_split(
    split_name: str,
    images_dir: Path,
    labels_dir: Path,
) -> dict:
    """Run verification checks on a single split. Returns stats dict."""
    stats = count_samples(images_dir, labels_dir)

    logger.info("--- %s ---", split_name)
    logger.info("  Images:           %d", stats["images"])
    logger.info("  Label files:      %d", stats["labels"])
    logger.info("  Non-empty labels: %d", stats["non_empty_labels"])

    # Check 1: image-label count mismatch
    if stats["images"] != stats["labels"]:
        logger.warning(
            "  MISMATCH: %d images vs %d label files",
            stats["images"], stats["labels"],
        )

    # Check 2: images without corresponding labels (use rglob for nested dirs)
    imgs = {p.stem for p in images_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}}
    lbls = {p.stem for p in labels_dir.rglob("*.txt") if p.is_file()}
    missing_labels = imgs - lbls
    missing_images = lbls - imgs
    if missing_labels:
        logger.warning("  Images missing labels: %d", len(missing_labels))
    if missing_images:
        logger.warning("  Labels missing images: %d", len(missing_images))

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify YOLO-seg dataset and generate preview images"
    )
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR,
                        help="Path to YOLO dataset directory")
    parser.add_argument("--preview-dir", type=Path, default=PREVIEW_DIR,
                        help="Directory to save preview images")
    parser.add_argument("--num-previews", type=int, default=5,
                        help="Number of preview images to generate")
    args = parser.parse_args()

    random.seed(42)

    all_stats: dict[str, dict] = {}
    images_root = args.dataset_dir / "images"
    labels_root = args.dataset_dir / "labels"

    # Clean old previews
    if args.preview_dir.exists():
        import shutil
        shutil.rmtree(args.preview_dir)
    args.preview_dir.mkdir(parents=True, exist_ok=True)

    for split in ["train", "val", "test"]:
        img_dir = images_root / split
        lbl_dir = labels_root / split
        if not img_dir.exists():
            continue
        stats = verify_split(split, img_dir, lbl_dir)
        all_stats[split] = stats

        previews = generate_previews(
            img_dir, lbl_dir, args.preview_dir,
            num_samples=min(args.num_previews, stats["images"]),
            split_name=split,
        )

    # Summary table
    logger.info("")
    logger.info("=" * 50)
    logger.info("  Dataset Summary")
    logger.info("=" * 50)
    for split, s in all_stats.items():
        logger.info(
            "  %-6s | images: %4d | labels: %4d | non-empty: %4d",
            split, s["images"], s["labels"], s["non_empty_labels"],
        )
    total_imgs = sum(s["images"] for s in all_stats.values())
    total_lbls = sum(s["labels"] for s in all_stats.values())
    logger.info("  %-6s | images: %4d | labels: %4d", "TOTAL", total_imgs, total_lbls)
    logger.info("")
    logger.info("Previews saved to: %s", args.preview_dir)


if __name__ == "__main__":
    main()
