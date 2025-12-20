from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user info with credits.
    Frontend calls this to show user email + credits balance.
    """
    user_id = current_user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            SELECT id, email, credits, plan, subscription_status
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            return {"error": "User not found"}, 404
        
        cur.close()
        conn.close()
        
        return {
            "id": user["id"],
            "email": user["email"],
            "credits": user.get("credits", 0),
            "plan": user.get("plan", "free"),
            "subscription_status": user.get("subscription_status")
        }
        
    except Exception as e:
        cur.close()
        conn.close()
        raise
