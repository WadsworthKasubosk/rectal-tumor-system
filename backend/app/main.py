"""FastAPI entry point — create app, mount routers, configure CORS."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import UPLOAD_DIR, REPORT_DIR, MODELS_DIR
from app.database import init_db
from app.api import auth, upload, inference, cases, reports

app = FastAPI(
    title="Rectal Tumor AI Diagnosis System",
    version="1.0.0",
    description="直肠肿瘤 AI 辅助诊断系统",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files — uploaded images, reports, samples
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/reports", StaticFiles(directory=str(REPORT_DIR)), name="reports")

# Mount routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(inference.router)
app.include_router(cases.router)
app.include_router(reports.router)

# Model listing endpoint
@app.get("/api/models")
def list_models():
    """Return available AI models with their status."""
    from app.config import AVAILABLE_MODELS
    result = []
    for m in AVAILABLE_MODELS:
        model_path = Path(m["path"])
        exists = model_path.exists()
        result.append({
            "name": m["name"],
            "label": m["label"],
            "available": exists,
            "size_mb": round(model_path.stat().st_size / 1e6, 1) if exists else 0,
        })
    return result


@app.on_event("startup")
def startup():
    """Initialize database and seed default admin."""
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "rectal-tumor-api"}
