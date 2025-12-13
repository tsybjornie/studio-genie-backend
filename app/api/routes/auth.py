from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.security import hash_password, verify_password, create_access_token
from app.core.database import db
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
async def register(payload: RegisterRequest):
    existing = (
        db.service_client
        .table("users")
        .select("id")
        .eq("email", payload.email)
        .execute()
    )

    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(payload.password)

    result = (
        db.service_client
        .table("users")
        .insert({
            "email": payload.email,
            "password_hash": hashed_password,
            "credits": 0
        })
        .execute()
    )

    if not result.data:
        logger.error("User insert failed")
        raise HTTPException(status_code=500, detail="Failed to create user")

    user_id = result.data[0]["id"]
    token = create_access_token({"user_id": user_id})

    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
async def login(payload: LoginRequest):
    logger.info(f"Login attempt for {payload.email}")

    try:
        result = (
            db.service_client
            .table("users")
            .select("id, password_hash")
            .eq("email", payload.email)
            .execute()
        )

        logger.info(f"DB result: {result}")

        if not result.data:
            logger.warning("User not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = result.data[0]

        if "password_hash" not in user or not user["password_hash"]:
            logger.error("password_hash missing in DB row")
            raise HTTPException(status_code=500, detail="User password not set")

        if not verify_password(payload.password, user["password_hash"]):
            logger.warning("Password mismatch")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"user_id": user["id"]})
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
