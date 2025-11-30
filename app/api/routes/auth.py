from fastapi import APIRouter, HTTPException, Depends
from app.schemas.auth_schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.core.database import get_db, SupabaseClient
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user
from datetime import timedelta
from app.core.config import settings
import uuid
import logging
import unicodedata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def sanitize_password(pwd: str) -> str:
    """
    Removes hidden characters, BOM markers, newlines, and normalizes the password.
    Ensures bcrypt never receives >72 bytes.
    """
    if not pwd:
        return pwd
    
    # Normalize unicode → remove hidden non-printable stuff
    pwd = unicodedata.normalize("NFKC", pwd)

    # Remove whitespace from edges
    pwd = pwd.strip()

    # Remove newline, tab, BOM, and non ASCII control chars
    cleaned = "".join(c for c in pwd if c.isprintable())

    # Enforce bcrypt’s 72-byte hard limit
    if len(cleaned.encode("utf-8")) > 72:
        cleaned = cleaned.encode("utf-8")[:72].decode("utf-8", errors="ignore")

    return cleaned


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: SupabaseClient = Depends(get_db)):
    try:
        # Sanitize password to avoid bcrypt crashes
        clean_password = sanitize_password(request.password)

        # Check if user exists
        existing = (
            db.service_client.table("users")
            .select("*")
            .eq("email", request.email)
            .execute()
        )

        if existing.data and len(existing.data) > 0:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash password safely
        try:
            hashed_password = get_password_hash(clean_password)
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Password hashing failed. Ensure password contains valid characters."
            )

        # Prepare user
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "email": request.email,
            "hashed_password": hashed_password,
            "has_trial_used": False,
            "credits_remaining": 0,
            "plan": None
        }

        # Insert into Supabase
        response = db.service_client.table("users").insert(user_data).execute()

        if hasattr(response, "error") and response.error:
            logger.error(f"Supabase insert error: {response.error}")
            raise HTTPException(status_code=500, detail="Database insert failed")

        # Generate JWT token
        access_token = create_access_token(
            data={"sub": user_id, "email": request.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(f"User registered: {request.email}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            email=request.email
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backend error: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: SupabaseClient = Depends(get_db)):
    try:
        # Lookup user
        result = db.service_client.table("users").select("*").eq("email", request.email).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user = result.data[0]

        # Sanitize incoming password for comparison
        clean_password = sanitize_password(request.password)

        if not verify_password(clean_password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Create token
        access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(f"Login successful: {request.email}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user["id"],
            email=user["email"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        has_trial_used=current_user["has_trial_used"],
        credits_remaining=current_user["credits_remaining"],
        plan=current_user.get("plan")
    )
