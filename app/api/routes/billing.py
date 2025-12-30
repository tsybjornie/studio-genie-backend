from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.stripe_service import stripe_service
from app.core.security import get_current_user
from app.core.config import settings
from app.core.subscription_prices import SUBSCRIPTION_PRICES

router = APIRouter(prefix="/billing", tags=["Billing"])


# Credit pack price IDs (for one-time purchases in dashboard)
CREDIT_PACK_PRICES = {
    "small": "price_1SdZ50BBwifSvpdIWW1Ntt22",
    "medium": "price_1SdZ7TBBwifSvpdIAZqbTuLR",
    "power": "price_1SdZ7xBBwifSvpdI1B6BjybU",
}


class SubscriptionCheckoutRequest(BaseModel):
    price_id: str


class CreditCheckoutRequest(BaseModel):
    pack_key: str


@router.post("/create-checkout-session")
def create_subscription_checkout(request: SubscriptionCheckoutRequest):
    """
    Create Stripe checkout for monthly subscription (from landing page pricing).
    No authentication required - for new users.
    After payment, redirect to signup page.
    """
    price_id = request.price_id
    
    if price_id not in SUBSCRIPTION_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid subscription price ID: {price_id}")

    try:
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            customer_email=None,  # User hasn't signed up yet
            user_id=None,
            success_url=f"{settings.FRONTEND_URL}/signup?subscription=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/pricing?cancelled=true",
            mode="subscription",
        )
        
        return {"url": session["url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post("/checkout/credits")
def create_credit_checkout(
    request: CreditCheckoutRequest,
    current_user=Depends(get_current_user),
):
    """
    Create Stripe checkout for one-time credit pack purchase (from dashboard).
    Requires authentication - for existing users.
    """
    pack_key = request.pack_key
    
    if pack_key not in CREDIT_PACK_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid credit pack: {pack_key}")

    price_id = CREDIT_PACK_PRICES[pack_key]
    
    user_id = current_user.get("user_id")
    user_email = current_user.get("email", "unknown@example.com")

    try:
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            customer_email=user_email,
            user_id=user_id,
            success_url=f"{settings.FRONTEND_URL}/dashboard?success=true",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard?cancelled=true",
            mode="payment",
        )
        
        return {"url": session["url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")
