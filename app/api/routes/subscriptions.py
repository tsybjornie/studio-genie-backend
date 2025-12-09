from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user
from app.models.subscription import Subscription
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("")
async def get_user_subscriptions(current_user: dict = Depends(get_current_user)):
    """
    Returns all subscription records for the authenticated user.
    """
    try:
        subs = Subscription.get_by_user_id(current_user["id"])
        return subs

    except Exception as e:
        logger.error(f"Error fetching subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscriptions")


@router.get("/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Returns a specific subscription for the authenticated user.
    """
    try:
        sub = Subscription.get(subscription_id)

        if not sub or sub.user_id != current_user["id"]:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return sub

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error fetching subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")
