from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.database import get_db, SupabaseClient
import unicodedata
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def sanitize_password(password: str) -> str:
    # Normalize unicode characters
    pwd = unicodedata.normalize("NFKC", password)
    # Keep only ascii printable set
    allowed = set(string.printable)
    pwd = "".join(ch for ch in pwd if ch in allowed)
    return pwd

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = sanitize_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    password = sanitize_password(password)
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: SupabaseClient = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    response = db.service_client.table("users").select("*").eq("id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=401, detail="User not found")

    return response.data[0]
