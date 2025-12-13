from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
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

    hashed = hash_password(payload.password)

    user = (
        db.service_client
        .table("users")
        .insert({
            "email": payload.email,
            "password_hash": hashed,
            "credits": 0
        })
        .execute()
    )

    token = create_access_token({"user_id": user.data[0]["id"]})
    return {"access_token": token}


@router.post("/login")
async def login(payload: LoginRequest):
    result = (
        db.service_client
        .table("users")
        .select("*")
        .eq("email", payload.email)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result.data

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user["id"]})
    return {"access_token": token}
