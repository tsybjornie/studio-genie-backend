"""
Stripe Checkout Routes - Canonical v1.0
Two separate endpoints: subscription (landing) and credits (dashboard)
POST-only, webhook-based credit grants
HARDENED: Explicit GET rejection with clear error messages
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.stripe_service import stripe_service
from app.core.security import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stripe", tags=["Stripe Checkout"])

# ========================================
# SUBSCRIPTION PRICES (Monthly Recurring)
# ========================================
SUBSCRIPTION_PRICES = {
    "price_1SV4tkBBwifSvpdICrbo1QFJ": {
        "name": "Starter",
        "monthly_credits": 12,  # 4 videos × 3 credits
    },
    "price_1SV4uUBBwifSvpdIuoSpX0Q2": {
        "name": "Creator",
        "monthly_credits": 36,  # 12 videos × 3 credits
    },
    "price_1SV4vLBBwifSvpdIYZlLeYJ6": {
        "name": "Pro",
        "monthly_credits": 90,  # 30 videos × 3 credits
    },
}

# ========================================
# CREDIT PACKS (One-time Purchase)
# ========================================
CREDIT_PACKS = {
    "small": {
        "price_id": "price_1SdZ5QBBwifSvpdIWW1Ntt22",
        "credits": 6,  # 2 videos × 3 credits
        "name": "Small Pack",
    },
    "medium": {
        "price_id": "price_1SdZ7TBBwifSvpdIAZqbTuLR",
        "credits": 15,  # 5 videos × 3 credits
        "name": "Medium Pack",
    },
    "power": {
        "price_id": "price_1SdZ7xBBwifSvpdI1B6BjybU",
        "credits": 24,  # 8 videos × 3 credits
        "name": "Power Pack",
    },
}


# ========================================
# REQUEST MODELS
# ========================================
class SubscriptionCheckoutRequest(BaseModel):
    priceId: str


class CreditCheckoutRequest(BaseModel):
    packKey: str


# ========================================
# ENDPOINT 1: SUBSCRIPTION CHECKOUT (POST)
# ========================================
@router.post("/checkout/subscription")
async def create_subscription_checkout(
    body: SubscriptionCheckoutRequest
):
    """
    Subscription checkout for landing page pricing.
    
    - No authentication required
    - User pays BEFORE registration
    - Stripe mode: 'subscription'
    - Redirects to registration page with session_id
    - Credits awarded via webhook (invoice.paid)
    """
    logger.info(f"[CHECKOUT] POST /checkout/subscription | PriceID: {body.priceId}")
    
    price_id = body.priceId
    
    # Validate price ID
    if price_id not in SUBSCRIPTION_PRICES:
        logger.error(f"[CHECKOUT] Invalid subscription price ID: {price_id}")
        raise HTTPException(status_code=400, detail=f"Invalid subscription price ID: {price_id}")
    
    plan_info = SUBSCRIPTION_PRICES[price_id]
    
    try:
        logger.info(f"[CHECKOUT] Creating subscription session | Plan: {plan_info['name']} | PriceID: {price_id}")
        
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            customer_email=None,  # User hasn't registered yet
            user_id=None,  # Will be linked after registration
            success_url=f"{settings.FRONTEND_URL}/register?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/pricing",
            mode="subscription",
        )
        
        logger.info(f"[CHECKOUT] ✅ 200 OK | Subscription session created | SessionID: {session.get('session_id')} | URL: {session.get('url')}")
        
        return {"url": session["url"]}
        
    except Exception as e:
        logger.error(f"[CHECKOUT] ❌ 500 ERROR | Subscription session creation failed | Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


# HARDENING: Explicit GET rejection for subscription
@router.get("/checkout/subscription")
async def reject_get_subscription():
    """Reject GET requests with clear error message"""
    logger.warning("[CHECKOUT] ❌ 405 | GET /checkout/subscription rejected - POST required")
    raise HTTPException(
        status_code=405, 
        detail="Method Not Allowed. This endpoint requires POST with JSON body: {\"priceId\": \"price_...\"}"
    )


# ========================================
# ENDPOINT 2: CREDIT PACK CHECKOUT (POST)
# ========================================
@router.post("/checkout/credits")
async def create_credit_checkout(
    body: CreditCheckoutRequest,
    current_user=Depends(get_current_user),
):
    """
    Credit pack checkout for authenticated dashboard users.
    
    - Authentication required (JWT in Authorization header)
    - User must be logged in
    - Stripe mode: 'payment' (one-time)
    - Redirects back to dashboard
    - Credits awarded via webhook (checkout.session.completed)
    """
    user_id = current_user.get("user_id")
    logger.info(f"[CHECKOUT] POST /checkout/credits | UserID: {user_id} | PackKey: {body.packKey}")
    
    pack_key = body.packKey
    
    # Validate pack key
    if pack_key not in CREDIT_PACKS:
        logger.error(f"[CHECKOUT] Invalid credit pack key: {pack_key}")
        raise HTTPException(status_code=400, detail=f"Invalid credit pack: {pack_key}")
    
    pack_info = CREDIT_PACKS[pack_key]
    price_id = pack_info["price_id"]
    
    user_email = current_user.get("email", "unknown@example.com")
    
    try:
        logger.info(f"[CHECKOUT] Creating credit pack session | UserID: {user_id} | Pack: {pack_info['name']} | Credits: {pack_info['credits']}")
        
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            customer_email=user_email,
            user_id=user_id,
            success_url=f"{settings.FRONTEND_URL}/dashboard/credits",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/credits",
            mode="payment",
        )
        
        logger.info(f"[CHECKOUT] ✅ 200 OK | Credit pack session created | UserID: {user_id} | SessionID: {session.get('session_id')}")
        
        return {"url": session["url"]}
        
    except Exception as e:
        logger.error(f"[CHECKOUT] ❌ 500 ERROR | Credit pack session creation failed | UserID: {user_id} | Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


# HARDENING: Explicit GET rejection for credits
@router.get("/checkout/credits")
async def reject_get_credits():
    """Reject GET requests with clear error message"""
    logger.warning("[CHECKOUT] ❌ 405 | GET /checkout/credits rejected - POST + JWT required")
    raise HTTPException(
        status_code=405, 
        detail="Method Not Allowed. This endpoint requires POST with Authorization header and JSON body: {\"packKey\": \"small|medium|power\"}"
    )
