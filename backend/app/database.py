"""SQLAlchemy database setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Ensure all ORM models are imported so they register with Base.metadata before create_all
import app.models.user    # noqa: E402
import app.models.case    # noqa: E402
import app.models.diagnosis  # noqa: E402


def init_db() -> None:
    """Create all tables and seed default admin account."""
    from app.models.user import User

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            from app.utils.hash_utils import hash_password
            admin = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                name="系统管理员",
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
