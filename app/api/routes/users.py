from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user info with real credits from database.
    """
    user_id = current_user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT id, email, credits FROM users WHERE id = %s",
        (user_id,)
    )
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if not result:
        return {
            "id": user_id,
            "email": "unknown",
            "credits": 0,
            "plan": "starter"
        }
    
    return {
        "id": result["id"],
        "email": result["email"],
        "credits": result["credits"] or 0,
        "plan": "starter"
    }
