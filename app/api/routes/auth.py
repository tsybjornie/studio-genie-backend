from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.security import hash_password, verify_password, create_access_token
from app.core.database import get_db
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
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE email = %s",
        (payload.email,)
    )
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(payload.password)

    cur.execute(
        """
        INSERT INTO users (email, password_hash, credits)
        VALUES (%s, %s, 0)
        RETURNING id
        """,
        (payload.email, hashed_password)
    )

    user_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()

    token = create_access_token({"user_id": user_id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
async def login(payload: LoginRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, password_hash FROM users WHERE email = %s",
        (payload.email,)
    )
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user["password_hash"]):
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    cur.close()
    conn.close()

    token = create_access_token({"user_id": user["id"]})
    return {"access_token": token, "token_type": "bearer"}
