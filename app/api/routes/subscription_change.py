from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user
from app.models.subscription import Subscription
from app.core.config import settings
import stripe

router = APIRouter(prefix="/subscription", tags=["Subscription"])

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/change")
async def change_subscription(
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    User requests upgrade/downgrade.
    Expected payload:
    {
        "new_price_id": "price_12345"
    }
    """
    new_price_id = payload.get("new_price_id")
    if not new_price_id:
        raise HTTPException(status_code=400, detail="Missing new_price_id")

    # Fetch existing subscription record in DB
    sub = Subscription.get_by_user_id(current_user["id"])
    if not sub:
        raise HTTPException(status_code=404, detail="Active subscription not found")

    try:
        # Stripe subscription update (auto prorations)
        # Note: In a real app we would await this if using async stripe client or run in threadpool
        # But stripe python client is synchronous. FastAPI handles sync routes in threadpool if def (not async def)
        # However, user provided `async def` and synchronous stripe call. 
        # This will block the event loop, but for low volume it's 'ok'.
        # ideally we'd wrap in run_in_executor or use async def without blocking calls.
        # Following user snippet exactly.
        
        updated = stripe.Subscription.modify(
            sub.stripe_subscription_id,
            items=[{
                "id": sub.stripe_item_id,
                "price": new_price_id
            }],
            proration_behavior="always_invoice"
        )

        # Update local DB
        sub.price_id = new_price_id
        # Safely get nickname or fallback
        sub.plan = updated["items"]["data"][0]["price"].get("nickname", "unknown")
        sub.save()

        return {
            "status": "success",
            "new_plan": sub.plan,
            "proration_applied": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
