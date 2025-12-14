from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password, create_access_token
from app.core.database import get_db
from app.models.user import User
import logging

router = APIRouter()
logger = logging.getLogger("auth")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(User.email == payload.email).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(payload.password)

    # Create new user
    new_user = User(
        email=payload.email,
        password_hash=hashed_password,
        credits=0
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"user_id": new_user.id})

    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for {payload.email}")

    try:
        # Query user by email
        user = db.query(User).filter(User.email == payload.email).first()

        if not user:
            logger.warning("User not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.password_hash:
            logger.error("password_hash missing in DB row")
            raise HTTPException(status_code=500, detail="User password not set")

        if not verify_password(payload.password, user.password_hash):
            logger.warning("Password mismatch")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"user_id": user.id})
        logger.info("Login success")

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("LOGIN CRASHED")
        raise HTTPException(status_code=500, detail=str(e))
