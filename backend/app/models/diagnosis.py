"""AI diagnosis record ORM model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.database import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, nullable=False, index=True)  # FK → cases.id
    image_filename = Column(String(255), nullable=False)
    image_path = Column(String(512), nullable=False)
    model_name = Column(String(50), nullable=False)
    detection_count = Column(Integer, default=0)
    max_confidence = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    inference_time_ms = Column(Float, default=0.0)
    result_json = Column(Text, default="{}")  # full JSON of boxes/masks/scores
    overlay_path = Column(String(512), nullable=True)  # rendered overlay image
    report_path = Column(String(512), nullable=True)  # PDF report
    created_at = Column(DateTime, default=datetime.utcnow)
