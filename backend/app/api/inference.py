"""Inference routes: AI diagnosis on uploaded images."""

import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, AVAILABLE_MODELS
from app.database import SessionLocal

router = APIRouter(prefix="/api", tags=["inference"])


class InferenceRequest(BaseModel):
    image_id: int
    model_name: str = "baseline"


class DetectionItem(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    mask_polygon: list[list[float]]  # [[x,y], ...] normalized
    area_pixels: int


class InferenceResponse(BaseModel):
    id: int
    image_id: int
    model_name: str
    detections: list[DetectionItem]
    detection_count: int
    max_confidence: float
    avg_confidence: float
    inference_time_ms: float
    image_size: list[int]  # [W, H]
    overlay_url: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/inference", response_model=InferenceResponse)
def run_inference(req: InferenceRequest, db: Session = Depends(get_db)):
    """Run AI inference on an uploaded image and return detection results."""
    from app.models.case import Case
    from app.models.diagnosis import Diagnosis

    # Find case image
    case = db.query(Case).filter(Case.id == req.image_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="病例不存在")

    # Find uploaded image
    uploads = list(UPLOAD_DIR.glob("*"))
    image_path = None
    for up in uploads:
        if up.is_file():
            image_path = up
            break
    if image_path is None:
        raise HTTPException(status_code=404, detail="图像文件不存在")

    # Find model config
    model_cfg = next((m for m in AVAILABLE_MODELS if m["name"] == req.model_name), None)
    if model_cfg is None:
        raise HTTPException(status_code=400, detail=f"模型 '{req.model_name}' 不存在")

    # Run inference
    from app.core.inference_engine import InferenceEngine
    engine = InferenceEngine(model_cfg["path"])
    result = engine.predict(str(image_path))

    # Save diagnosis record
    import json
    diag = Diagnosis(
        case_id=case.id,
        image_filename=image_path.name,
        image_path=str(image_path),
        model_name=req.model_name,
        detection_count=len(result.get("boxes", [])),
        max_confidence=max(result.get("scores", [0])),
        avg_confidence=sum(result.get("scores", [])) / max(len(result.get("scores", [])), 1),
        inference_time_ms=result.get("inference_time_ms", 0),
        result_json=json.dumps(result),
    )
    db.add(diag)
    db.commit()
    db.refresh(diag)

    # Build detection items
    detections = []
    boxes = result.get("boxes", [])
    masks = result.get("masks", [])
    scores = result.get("scores", [])
    for i in range(len(boxes)):
        det = DetectionItem(
            x1=boxes[i][0], y1=boxes[i][1], x2=boxes[i][2], y2=boxes[i][3],
            confidence=round(scores[i], 4),
            mask_polygon=masks[i] if i < len(masks) else [],
            area_pixels=0,
        )
        detections.append(det)

    return InferenceResponse(
        id=diag.id,
        image_id=case.id,
        model_name=req.model_name,
        detections=detections,
        detection_count=diag.detection_count,
        max_confidence=diag.max_confidence,
        avg_confidence=diag.avg_confidence,
        inference_time_ms=result["inference_time_ms"],
        image_size=result.get("image_size", [0, 0]),
        overlay_url=None,
    )


# ---------------------------------------------------------------------------
# Multi-model comparison endpoint
# ---------------------------------------------------------------------------

class CompareModelResult(BaseModel):
    model_name: str
    model_label: str
    detections: int
    max_confidence: float
    inference_time_ms: float
    overlay_url: str | None = None
    image_size: list[int] = [0, 0]
    status: str = "success"
    error: str | None = None


class CompareResponse(BaseModel):
    image_id: str
    image_url: str
    results: dict[str, CompareModelResult]  # keyed by model name
    fastest_model: str | None = None
    highest_conf_model: str | None = None
    total_time_ms: float


@router.post("/inference/compare", response_model=CompareResponse)
async def compare_models(file: UploadFile = File(...)):
    """Run all 4 AI models on the same image and return side-by-side results."""
    from app.core.inference_engine import InferenceEngine

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    # Save uploaded image
    image_id = uuid.uuid4().hex[:12]
    ext = Path(file.filename or "img.jpg").suffix or ".jpg"
    save_path = UPLOAD_DIR / f"{image_id}{ext}"
    content = await file.read()
    save_path.write_bytes(content)

    results: dict[str, CompareModelResult] = {}
    overall_start = time.perf_counter()

    for model_cfg in AVAILABLE_MODELS:
        model_name = model_cfg["name"]
        model_label = model_cfg["label"]
        try:
            engine = InferenceEngine(model_cfg["path"])
            t0 = time.perf_counter()
            pred = engine.predict(str(save_path))
            elapsed = (time.perf_counter() - t0) * 1000.0

            # Generate overlay image
            overlay = engine.visualize(str(save_path), mode="both")
            overlay_name = f"{image_id}_{model_name}.png"
            overlay_path = UPLOAD_DIR / overlay_name
            overlay.save(str(overlay_path), format="PNG")

            scores = pred.get("scores", [])
            results[model_name] = CompareModelResult(
                model_name=model_name,
                model_label=model_label,
                detections=len(pred.get("boxes", [])),
                max_confidence=round(max(scores), 4) if scores else 0.0,
                inference_time_ms=round(elapsed, 1),
                overlay_url=f"/uploads/{overlay_name}",
                image_size=pred.get("image_size", [0, 0]),
                status="success",
            )
            engine.unload()
        except Exception as exc:
            results[model_name] = CompareModelResult(
                model_name=model_name,
                model_label=model_label,
                detections=0,
                max_confidence=0.0,
                inference_time_ms=0.0,
                status="error",
                error=str(exc),
            )

    total_ms = round((time.perf_counter() - overall_start) * 1000.0, 1)

    successful = {k: v for k, v in results.items() if v.status == "success"}
    fastest = min(successful.items(), key=lambda x: x[1].inference_time_ms, default=(None, None))
    highest = max(successful.items(), key=lambda x: x[1].max_confidence, default=(None, None))

    return CompareResponse(
        image_id=image_id,
        image_url=f"/uploads/{save_path.name}",
        results=results,
        fastest_model=fastest[0],
        highest_conf_model=highest[0],
        total_time_ms=total_ms,
    )
