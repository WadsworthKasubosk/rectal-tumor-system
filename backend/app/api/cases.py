"""Case management routes: list, detail, stats."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.case import Case
from app.models.diagnosis import Diagnosis

router = APIRouter(prefix="/api", tags=["cases"])


class CaseSummary(BaseModel):
    id: int
    patient_name: str
    patient_gender: str | None
    patient_age: int | None
    exam_date: str
    exam_type: str
    diagnosis_count: int = 0
    latest_result: str | None = None  # positive / negative / pending

    class Config:
        from_attributes = True


class CaseDetail(CaseSummary):
    notes: str | None
    doctor_name: str | None
    diagnoses: list[dict]

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: list[CaseSummary]
    total: int
    page: int
    page_size: int


class DashboardStats(BaseModel):
    total_cases: int
    total_diagnoses: int
    positive_count: int
    negative_count: int
    avg_confidence: float
    model_usage: dict  # {model_name: count}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/cases", response_model=PaginatedResponse)
def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db),
):
    """List cases with pagination and optional search by patient name."""
    query = db.query(Case)
    if search:
        query = query.filter(Case.patient_name.contains(search))
    total = query.count()
    cases = query.order_by(Case.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = []
    for c in cases:
        diag_count = db.query(Diagnosis).filter(Diagnosis.case_id == c.id).count()
        latest_diag = (
            db.query(Diagnosis)
            .filter(Diagnosis.case_id == c.id)
            .order_by(Diagnosis.created_at.desc())
            .first()
        )
        result = "pending"
        if latest_diag:
            result = "positive" if latest_diag.detection_count > 0 else "negative"

        items.append(CaseSummary(
            id=c.id, patient_name=c.patient_name,
            patient_gender=c.patient_gender, patient_age=c.patient_age,
            exam_date=c.created_at.isoformat(), exam_type=c.exam_type,
            diagnosis_count=diag_count, latest_result=result,
        ))

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Get a single case with all its diagnoses."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="病例不存在")

    diagnoses = (
        db.query(Diagnosis)
        .filter(Diagnosis.case_id == case_id)
        .order_by(Diagnosis.created_at.desc())
        .all()
    )

    return CaseDetail(
        id=case.id, patient_name=case.patient_name,
        patient_gender=case.patient_gender, patient_age=case.patient_age,
        exam_date=case.created_at.isoformat(), exam_type=case.exam_type,
        notes=case.notes, doctor_name="默认管理员",
        diagnosis_count=len(diagnoses),
        latest_result="positive" if any(d.detection_count > 0 for d in diagnoses) else "negative",
        diagnoses=[{
            "id": d.id,
            "image_filename": d.image_filename,
            "model_name": d.model_name,
            "detection_count": d.detection_count,
            "max_confidence": d.max_confidence,
            "avg_confidence": d.avg_confidence,
            "inference_time_ms": d.inference_time_ms,
            "created_at": d.created_at.isoformat(),
        } for d in diagnoses],
    )


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    """Aggregate dashboard statistics."""
    total_cases = db.query(Case).count()
    total_diagnoses = db.query(Diagnosis).count()
    positive = db.query(Diagnosis).filter(Diagnosis.detection_count > 0).count()
    negative = total_diagnoses - positive

    diags = db.query(Diagnosis).all()
    avg_conf = sum(d.avg_confidence for d in diags) / max(len(diags), 1)

    model_usage: dict[str, int] = {}
    for d in diags:
        model_usage[d.model_name] = model_usage.get(d.model_name, 0) + 1

    return DashboardStats(
        total_cases=total_cases,
        total_diagnoses=total_diagnoses,
        positive_count=positive,
        negative_count=negative,
        avg_confidence=round(avg_conf, 4),
        model_usage=model_usage,
    )
