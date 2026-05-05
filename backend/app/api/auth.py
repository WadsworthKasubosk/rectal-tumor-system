"""Auth routes: login / register."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    role: str = "doctor"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    name: str
    role: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    from app.utils.hash_utils import verify_password
    from datetime import datetime, timedelta
    from jose import jwt
    from app.models.user import User
    from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    payload = {
        "sub": user.username,
        "name": user.name,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return TokenResponse(
        access_token=token,
        username=user.username,
        name=user.name,
        role=user.role,
    )


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new doctor account."""
    from app.utils.hash_utils import verify_password
    from datetime import datetime, timedelta
    from jose import jwt
    from app.models.user import User
    from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    from app.utils.hash_utils import hash_password
    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        name=req.name,
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    payload = {
        "sub": user.username,
        "name": user.name,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return TokenResponse(
        access_token=token,
        username=user.username,
        name=user.name,
        role=user.role,
    )
