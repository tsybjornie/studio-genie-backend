from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_connection
import logging

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


class GrantCreditsRequest(BaseModel):
    email: str
    credits: int


@router.post("/grant-credits")
async def grant_credits(payload: GrantCreditsRequest):
    """
    Admin endpoint to manually grant credits for testing.
    USE FOR TESTING ONLY - NOT FOR PRODUCTION.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Update credits
        cur.execute(
            "UPDATE users SET credits = %s WHERE email = %s",
            (payload.credits, payload.email)
        )
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"User {payload.email} not found")
        
        conn.commit()
        
        # Verify
        cur.execute(
            "SELECT email, credits FROM users WHERE email = %s",
            (payload.email,)
        )
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        logger.info(f"[ADMIN] Granted {payload.credits} credits to {payload.email}")
        
        return {
            "success": True,
            "email": result["email"],
            "credits": result["credits"],
            "message": f"Successfully granted {payload.credits} credits"
        }
        
    except Exception as e:
        logger.error(f"[ADMIN] Error granting credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))
