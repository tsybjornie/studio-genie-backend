from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user info with real credits and subscription status from database.
    Always returns email, subscription_status, and subscription_plan.
    """
    user_id = current_user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Query ALL required fields including subscription data
    cur.execute(
        """
        SELECT id, email, credits, subscription_status, subscription_plan 
        FROM users 
        WHERE id = %s
        """,
        (user_id,)
    )
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if not result:
        # User not found - return safe defaults
        return {
            "id": user_id,
            "email": "unknown@example.com",
            "credits": 0,
            "subscription_status": None,
            "subscription_plan": None
        }
    
    # Return all fields with safe defaults for null values
    return {
        "id": result["id"],
        "email": result.get("email") or "unknown@example.com",
        "credits": result.get("credits") or 0,
        "subscription_status": result.get("subscription_status"),  # Can be "active", "inactive", or None
        "subscription_plan": result.get("subscription_plan")  # Can be plan name or None
    }
