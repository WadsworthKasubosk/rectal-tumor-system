"""User ORM model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(String(20), default="doctor")  # admin | doctor
    created_at = Column(DateTime, default=datetime.utcnow)
