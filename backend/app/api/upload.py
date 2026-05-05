"""Upload routes: image upload for diagnosis."""

import uuid
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB
from app.database import SessionLocal

router = APIRouter(prefix="/api", tags=["upload"])


class UploadResponse(BaseModel):
    id: int
    filename: str
    url: str
    size_bytes: int
    created_at: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    patient_name: str = "",
    patient_gender: str = "",
    patient_age: int = 0,
    db: Session = Depends(get_db),
):
    """Upload an endoscopic image and create a case record."""
    # Validate
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件大小超过 {MAX_UPLOAD_SIZE_MB}MB")

    # Save file
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix or ".jpg"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / stored_name
    with open(file_path, "wb") as f:
        f.write(content)

    # Create case record
    from app.models.case import Case
    case = Case(
        patient_name=patient_name or "未知",
        patient_gender=patient_gender,
        patient_age=patient_age,
        exam_type="直肠镜",
        doctor_id=1,  # default admin
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return UploadResponse(
        id=case.id,
        filename=stored_name,
        url=f"/uploads/{stored_name}",
        size_bytes=len(content),
        created_at=case.created_at.isoformat(),
    )
