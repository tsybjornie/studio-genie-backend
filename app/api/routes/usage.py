from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.core.database import db
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
    return {
        "plan": user["plan"],
        "credits": user["credits_remaining"],
        "subscription_status": user["subscription_status"],
        "renewal_date": user["renewal_date"]
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
    current_credits = user["credits_remaining"]

    # SUBSCRIPTIONS — OPTIONAL RULE (customizable)
    if user["subscription_status"] == "active":
        # *Example rule:*
        # Subscriptions deduct 50% credits instead of full price
        amount = int(amount * 0.5)

    # Block negative credits
    if current_credits < amount:
        raise HTTPException(
            402,
            "Not enough credits → redirect user to checkout"
        )

    new_balance = current_credits - amount

    db.service_client.table("users").update({
        "credits_remaining": new_balance
    }).eq("id", user["id"]).execute()

    return {
        "status": "ok",
        "used": amount,
        "remaining": new_balance
    }
