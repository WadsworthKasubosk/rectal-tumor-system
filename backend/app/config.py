"""Application configuration — loaded from environment or defaults."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# --- Database ---
DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data.db'}"

# --- JWT ---
SECRET_KEY: str = "rectal-tumor-secret-change-in-production"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

# --- Models ---
MODELS_DIR: Path = BASE_DIR / "weights"

AVAILABLE_MODELS: list[dict] = [
    {"name": "baseline",     "path": str(MODELS_DIR / "baseline_best.pt"),   "label": "YOLO11s-seg Baseline"},
    {"name": "exp2_p2",      "path": str(MODELS_DIR / "exp2_p2_best.pt"),    "label": "+P2 Enhancement"},
    {"name": "exp3_cbam",    "path": str(MODELS_DIR / "exp3_cbam_best.pt"),  "label": "+CBAM Attention"},
    {"name": "exp4_p2_cbam", "path": str(MODELS_DIR / "improved_best.pt"),   "label": "+P2 + CBAM (Best)"},
]

# --- Upload ---
UPLOAD_DIR: Path = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE_MB: int = 10

# --- Report ---
REPORT_DIR: Path = BASE_DIR / "reports"
