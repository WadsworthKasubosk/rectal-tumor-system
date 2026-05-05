"""Report routes: PDF generation and download."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import REPORT_DIR
from app.database import SessionLocal
from app.models.case import Case
from app.models.diagnosis import Diagnosis

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    doctor_notes: str = ""


class ReportResponse(BaseModel):
    report_id: int
    filename: str
    download_url: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{case_id}", response_model=ReportResponse)
def generate_report(case_id: int, req: ReportRequest, db: Session = Depends(get_db)):
    """Generate a PDF report for a case and attach the latest diagnosis."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="病例不存在")

    diag = (
        db.query(Diagnosis)
        .filter(Diagnosis.case_id == case_id)
        .order_by(Diagnosis.created_at.desc())
        .first()
    )
    if not diag:
        raise HTTPException(status_code=400, detail="该病例暂无诊断记录")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"report_{case_id}_{diag.id}.pdf"
    report_path = REPORT_DIR / filename

    from app.core.pdf_generator import generate_pdf_report
    generate_pdf_report(case, diag, req.doctor_notes, str(report_path))

    diag.report_path = str(report_path)
    db.commit()

    return ReportResponse(
        report_id=diag.id,
        filename=filename,
        download_url=f"/api/reports/{case_id}/download",
    )


@router.get("/{case_id}/download")
def download_report(case_id: int, db: Session = Depends(get_db)):
    """Download the latest PDF report for a case."""
    diag = (
        db.query(Diagnosis)
        .filter(Diagnosis.case_id == case_id)
        .order_by(Diagnosis.created_at.desc())
        .first()
    )
    if not diag or not diag.report_path:
        raise HTTPException(status_code=404, detail="报告不存在，请先生成报告")

    return FileResponse(diag.report_path, filename=f"report_{case_id}.pdf")
