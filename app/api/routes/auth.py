from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register_user(payload: RegisterRequest):
    # Simple safety check for now
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # TODO: hook up to real DB / users table
    # For now we just pretend it succeeded so frontend can move on
    return {
        "status": "ok",
        "message": "Account created (stub). Backend wiring works.",
        "email": payload.email,
    }


@router.post("/login")
async def login_user(payload: LoginRequest):
    # TODO: real auth. For now just accept anything.
    return {
        "status": "ok",
        "message": "Login successful (stub).",
        "email": payload.email,
        "token": "fake-jwt-token"
    }
