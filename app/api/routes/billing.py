from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.stripe_service import stripe_service
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/billing", tags=["Billing"])


class CreditCheckoutRequest(BaseModel):
    pack_key: str  # "small" | "medium" | "power"


PRICE_MAP = {
    "small": "price_1SdZ5QBBwifSvpdIWW1Ntt22",
    "medium": "price_1SdZ7TBBwifSvpdIAZqbTuLR",
    "power": "price_1SdZ7xBBwifSvpdI1B6BjybU",
}


@router.post("/checkout/credits")
def checkout_credits(
    payload: CreditCheckoutRequest,
    user=Depends(get_current_user),
):
    """
    Create a Stripe Checkout session for credit purchase.
    Returns a session URL to redirect the user to Stripe.
    """
    price_id = PRICE_MAP.get(payload.pack_key)
    if not price_id:
        raise ValueError("Invalid credit pack")

    user_id = user.get("user_id")
    user_email = user.get("email", "unknown@example.com")

    session = stripe_service.create_checkout_session(
        price_id=price_id,
        customer_email=user_email,
        user_id=user_id,
        success_url=f"{settings.FRONTEND_URL}/dashboard?paid=1",
        cancel_url=f"{settings.FRONTEND_URL}/dashboard?canceled=1",
        mode="payment",
    )

    return session
