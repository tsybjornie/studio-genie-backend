from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_connection
from app.core.security import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user info - NO FALLBACKS.
    Returns exact database values for: id, email, credits, subscription_status, subscription_plan.
    Raises 404 if user not found.
    """
    user_id = current_user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Query ALL required fields
        cur.execute(
            """
            SELECT id, email, credits, subscription_status, subscription_plan 
            FROM users 
            WHERE id = %s
            """,
            (user_id,)
        )
        result = cur.fetchone()
        
        if not result:
            logger.error(f"[/users/me] User not found for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return EXACT database values (NO fallbacks, NO placeholders)
        return {
            "id": result["id"],
            "email": result["email"],  # Real email or NULL
            "credits": result["credits"] if result["credits"] is not None else 0,
            "subscription_status": result["subscription_status"],  # NULL, 'inactive', or 'active'
            "subscription_plan": result["subscription_plan"]  # NULL or plan name
        }
        
    finally:
        cur.close()
        conn.close()

