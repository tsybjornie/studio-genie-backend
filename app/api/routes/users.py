from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user info.
    Stub endpoint - returns hardcoded data.
    """
    return {
        "id": current_user.get("user_id"),
        "email": "test@studio-genie.com",
        "credits": 0,
        "plan": "starter"
    }
