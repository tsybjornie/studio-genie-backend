from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.database import get_connection
from app.core.security import hash_password, verify_password, create_access_token
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
        from datetime import datetime

        hashed_password = hash_password(data.password)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users (email, password_hash, credits, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (data.email, hashed_password, 0, datetime.utcnow())
        )

        user_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()

        token = create_access_token({"user_id": user_id})
        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        logging.error("REGISTER ERROR")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
def login(data: LoginRequest):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (data.email,)
        )
        user = cur.fetchone()

        if not user:
            cur.close()
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(data.password, user["password_hash"]):
            cur.close()
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid credentials")

        cur.close()
        conn.close()

        token = create_access_token({"user_id": user["id"]})
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error("LOGIN ERROR")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
