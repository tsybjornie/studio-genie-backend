from fastapi import APIRouter, Depends, HTTPException
from app.services.stripe_service import stripe_service
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/billing", tags=["Billing"])

# Map pack keys to Stripe price IDs
CREDIT_PACK_PRICES = {
    "small": "price_1SdZ5QBBwifSvpdIWW1Ntt22",
    "medium": "price_1SdZ7TBBwifSvpdIAZqbTuLR",
    "power": "price_1SdZ7xBBwifSvpdI1B6BjybU",
}


@router.post("/checkout/credits")
def create_credit_checkout(
    pack_key: str,
    current_user=Depends(get_current_user),
):
    """
    Create Stripe checkout session for credit pack purchase.
    
    Args:
        pack_key: "small" | "medium" | "power"
    """
    if pack_key not in CREDIT_PACK_PRICES:
        raise HTTPException(status_code=400, detail="Invalid credit pack")

    price_id = CREDIT_PACK_PRICES[pack_key]
    
    user_id = current_user.get("user_id")
    user_email = current_user.get("email", "unknown@example.com")

    session = stripe_service.create_checkout_session(
        price_id=price_id,
        customer_email=user_email,
        user_id=user_id,
        success_url=f"{settings.FRONTEND_URL}/dashboard?success=true",
        cancel_url=f"{settings.FRONTEND_URL}/dashboard?cancelled=true",
        mode="payment",
    )

    return session
