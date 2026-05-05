"""Download medical imaging datasets with progress bars and resume support.

Supports: Kvasir-SEG, CVC-ClinicDB, CVC-ColonDB, ETIS-LaribPolypDB.
Handles zip, tar.gz, and rar archives.
"""

import argparse
import logging
import shutil
import subprocess
import sys
import tarfile
import urllib3
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parent.parent / "datasets" / "raw"

DATASETS: dict[str, dict] = {
    "kvasir-seg": {
        "url": "https://datasets.simula.no/downloads/kvasir-seg.zip",
        "filename": "kvasir-seg.zip",
        "extract_subdir": "Kvasir-SEG",
        "note": "官网直链 - 训练用全量数据集 (1000 张)",
    },
    "cvc-clinicdb": {
        "url": "https://www.dropbox.com/s/p5qe9eotetjnbmq/CVC-ClinicDB.zip?dl=1",
        "filename": "CVC-ClinicDB.rar",
        "extract_subdir": "CVC-ClinicDB",
        "note": "Dropbox 镜像 (RAR 格式) - 训练用全量数据集 (612 张)",
    },
    "pranet-test-pack": {
        "url": "https://drive.google.com/file/d/1Y2z7FD5p5y31vkZwQQomXFRB0HutHyao/view?usp=sharing",
        "filename": "PraNet_TestPack.zip",
        "extract_subdir": "TestDataset",
        "gdrive_id": "1Y2z7FD5p5y31vkZwQQomXFRB0HutHyao",
        "note": "PraNet 作者整合包 (327MB) — 含 CVC-300/CVC-ClinicDB/CVC-ColonDB/ETIS/Kvasir 五个测试集，社区标准",
    },
    "cvc-colondb": {
        "url": "https://www.dropbox.com/s/at28n1h85r3k2ew/CVC-ColonDB.zip?dl=1",
        "filename": "CVC-ColonDB.zip",
        "extract_subdir": "CVC-ColonDB",
        "note": "备选: 单独下载 ColonDB (如不用 PraNet 整合包)",
    },
    "etis-laribpolypdb": {
        "url": "https://www.dropbox.com/s/j4nsxijf5dhzb6w/ETIS-LaribPolypDB.rar?dl=1",
        "filename": "ETIS-LaribPolypDB.rar",
        "extract_subdir": "ETIS-LaribPolypDB",
        "note": "备选: 单独下载 ETIS (如不用 PraNet 整合包)",
    },
}


def download_gdrive(file_id: str, dest: Path) -> bool:
    """Download from Google Drive using gdown. Returns True on success."""
    try:
        import gdown
        gdown.download(id=file_id, output=str(dest), quiet=False)
        if dest.exists() and dest.stat().st_size > 1000:
            logger.info("  -> saved %s (%s bytes)", dest.name, dest.stat().st_size)
            return True
        return False
    except ImportError:
        logger.error("gdown not installed – run: pip install gdown")
        return False
    except Exception as e:
        logger.error("gdown download failed: %s", e)
        return False


def download_file(url: str, dest: Path) -> bool:
    """Download a file with progress bar and resume support.

    Returns True on success, False on failure.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers: dict[str, str | int] = {}
    existing_size = 0

    if dest.exists():
        existing_size = dest.stat().st_size
        if existing_size > 0:
            headers["Range"] = f"bytes={existing_size}-"

    try:
        with requests.get(url, stream=True, timeout=60, headers=headers, verify=False) as resp:
            if resp.status_code not in (200, 206):
                logger.error("HTTP %s for %s", resp.status_code, url)
                return False

            total = int(resp.headers.get("content-length", 0))
            mode = "ab" if resp.status_code == 206 else "wb"
            desc = f"  {dest.name}"

            with open(dest, mode) as f:
                with tqdm(total=total + existing_size if mode == "ab" else total,
                          initial=existing_size if mode == "ab" else 0,
                          unit="B", unit_scale=True, desc=desc) as pbar:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        logger.info("  -> saved %s (%s bytes)", dest.name, dest.stat().st_size)
        return True
    except requests.RequestException as e:
        logger.error("Download failed: %s  URL: %s", e, url)
        return False


def _is_html_file(path: Path) -> bool:
    """Check if downloaded file is actually an HTML error page."""
    try:
        with open(path, "rb") as f:
            head = f.read(128)
        return head.lstrip().startswith(b"<!DOCTYPE") or head.lstrip().startswith(b"<html")
    except OSError:
        return False


def _extract_rar(path: Path, extract_to: Path) -> bool:
    """Extract RAR archive using patool or unrar CLI."""
    # Try patoolib first (most portable)
    try:
        import patoolib
        patoolib.extract_archive(str(path), outdir=str(extract_to))
        return True
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: unrar / winrar CLI
    for cmd in ["unrar", "C:\\Program Files\\WinRAR\\UnRAR.exe", "C:\\Program Files (x86)\\WinRAR\\UnRAR.exe"]:
        try:
            subprocess.run(
                [cmd, "x", "-o+", str(path), str(extract_to) + "\\"],
                check=True, capture_output=True,
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    logger.warning("Cannot extract RAR – install patool (`pip install patool`) or WinRAR")
    return False


def extract_archive(path: Path, extract_to: Path) -> bool:
    """Extract zip/tar.gz/rar to target directory. Returns True on success.

    Also deletes the archive file if it's an HTML error page.
    """
    if _is_html_file(path):
        logger.error("Downloaded file is HTML, not an archive. Deleting: %s", path.name)
        path.unlink()
        return False

    try:
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(extract_to)
        elif path.suffix.lower() == ".rar":
            if not _extract_rar(path, extract_to):
                return False
        elif path.suffixes[-2:] == [".tar", ".gz"] or path.suffix in (".gz", ".tgz"):
            with tarfile.open(path, "r:gz") as tf:
                tf.extractall(extract_to)
        else:
            logger.warning("Unknown archive format: %s", path.suffix)
            return False
        logger.info("  -> extracted to %s", extract_to)
        return True
    except zipfile.BadZipFile:
        logger.error("File is not a valid zip: %s", path.name)
        return False
    except Exception as e:
        logger.error("Extract failed for %s: %s", path, e)
        return False


def download_dataset(name: str, dry_run: bool = False) -> None:
    """Download and extract a single dataset by name."""
    if name not in DATASETS:
        logger.warning("Unknown dataset '%s', available: %s", name, list(DATASETS))
        return

    info = DATASETS[name]
    logger.info("=== %s ===", name)
    logger.info("  %s", info["note"])

    if dry_run:
        logger.info("  [dry-run] would download %s", info["url"])
        return

    archive_path = RAW_DIR / info["filename"]
    extract_dir = RAW_DIR

    if "gdrive_id" in info:
        if not download_gdrive(info["gdrive_id"], archive_path):
            return
    else:
        if not download_file(info["url"], archive_path):
            return

    extract_archive(archive_path, extract_dir)

    # Post-extract: handle nested directory
    nested = extract_dir / info["extract_subdir"]
    if nested.exists() and nested.is_dir():
        logger.info("  -> found nested %s/", info["extract_subdir"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Download rectal tumor datasets")
    parser.add_argument("--dataset", type=str, default=None,
                        help="Download a specific dataset (kvasir-seg, cvc-clinicdb, cvc-colondb, etis-laribpolypdb)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print URLs without downloading")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if args.dataset:
        download_dataset(args.dataset.lower(), dry_run=args.dry_run)
    else:
        for name in DATASETS:
            download_dataset(name, dry_run=args.dry_run)

    logger.info("All downloads complete.")


if __name__ == "__main__":
    main()
