from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.core.database import get_connection
from datetime import datetime

router = APIRouter(prefix="/usage", tags=["Usage"])


# ------------------------------------------------------------
# CHECK USER BALANCE
# ------------------------------------------------------------
@router.get("/balance")
async def get_balance(user=Depends(get_current_user)):
    """
    Returns the user's plan + credits.
    Every frontend will call this before generation.
    """
    user_id = user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """
        SELECT plan, credits, subscription_status, renewal_date 
        FROM users 
        WHERE id = %s
        """,
        (user_id,)
    )
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "plan": user_data["plan"] or "free",
        "credits": user_data["credits"] or 0,
        "subscription_status": user_data["subscription_status"] or "inactive",
        "renewal_date": user_data["renewal_date"]
    }


# ------------------------------------------------------------
# CONSUME CREDITS
# ------------------------------------------------------------
@router.post("/consume")
async def consume_credits(
    amount: int,
    user=Depends(get_current_user)
):
    """
    Deduct credits when a user generates a video/image/task.
    """
    user_id = user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get current user data
    cur.execute(
        """
        SELECT credits, subscription_status 
        FROM users 
        WHERE id = %s
        """,
        (user_id,)
    )
    user_data = cur.fetchone()
    
    if not user_data:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    current_credits = user_data["credits"] or 0

    # SUBSCRIPTIONS — OPTIONAL RULE (customizable)
    if user_data["subscription_status"] == "active":
        # *Example rule:*
        # Subscriptions deduct 50% credits instead of full price
        amount = int(amount * 0.5)

    # Block negative credits
    if current_credits < amount:
        cur.close()
        conn.close()
        raise HTTPException(
            402,
            "Not enough credits → redirect user to checkout"
        )

    new_balance = current_credits - amount

    cur.execute(
        "UPDATE users SET credits = %s WHERE id = %s",
        (new_balance, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "status": "ok",
        "used": amount,
        "remaining": new_balance
    }
