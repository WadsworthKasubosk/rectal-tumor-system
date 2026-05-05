"""Patient case ORM model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_name = Column(String(50), nullable=False)
    patient_gender = Column(String(10), nullable=True)  # 男/女
    patient_age = Column(Integer, nullable=True)
    exam_date = Column(DateTime, default=datetime.utcnow)
    exam_type = Column(String(50), default="直肠镜")
    notes = Column(Text, default="")
    doctor_id = Column(Integer, nullable=False)  # FK → users.id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
