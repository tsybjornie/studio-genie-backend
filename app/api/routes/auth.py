from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.database import get_connection
import traceback
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(data: RegisterRequest):
    try:
        import bcrypt
        from datetime import datetime

        password_hash = bcrypt.hashpw(
            data.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users (email, password_hash, credits, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (data.email, password_hash, 0, datetime.utcnow())
        )

        user_id = cur.fetchone()["id"]
        conn.commit()

        return {"id": user_id, "email": data.email}

    except Exception as e:
        logging.error("REGISTER ERROR")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
def login(data: LoginRequest):
    try:
        import bcrypt
        from jose import jwt
        import os

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (data.email,)
        )
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, email, password_hash = user

        if not bcrypt.checkpw(
            data.password.encode("utf-8"),
            password_hash.encode("utf-8")
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")

        token = jwt.encode(
            {"sub": email},
            SECRET_KEY,
            algorithm="HS256"
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except Exception as e:
        logging.error("LOGIN ERROR")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
