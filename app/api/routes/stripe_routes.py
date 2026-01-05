"""
Stripe Checkout Routes - Canonical v1.0
Subscription-gated checkout with authentication
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.stripe_service import stripe_service
from app.core.security import get_current_user
from app.core.subscription import require_active_subscription
from app.core.config import settings
from app.core.subscription_prices import SUBSCRIPTION_PRICES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stripe", tags=["Stripe Checkout"])



# ========================================
# CREDIT PACKS (One-time Purchase)
# ========================================
CREDIT_PACKS = {
    "small": {
        "price_id": "price_1SdZ50BBwifSvpdIWW1Ntt22",
        "credits": 9,  # Small - $25
        "name": "Small Pack",
    },
    "medium": {
        "price_id": "price_1SdZ7TBBwifSvpdIAZqbTuLR",
        "credits": 30,  # Medium - $65
        "name": "Medium Pack",
    },
    "power": {
        "price_id": "price_1SdZ7xBBwifSvpdI1B6BjybU",
        "credits": 90,  # Power - $119
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
    body: SubscriptionCheckoutRequest,
    current_user=Depends(get_current_user)  # ← Require authentication
):
    """
    Subscription checkout - Auth required.
    
    Flow: User must register/login BEFORE subscribing
    - Authentication required
    - User linked immediately in Stripe session
    - Stripe mode: 'subscription'
    - Credits awarded via webhook (invoice.paid)
    """
    user_id = current_user["user_id"]
    user_email = current_user.get("email", "unknown@example.com")  # Safe access with default
    
    logger.info(f"[CHECKOUT] POST /checkout/subscription | UserID: {user_id} | PriceID: {body.priceId}")
    
    price_id = body.priceId
    
    # Validate price ID
    if price_id not in SUBSCRIPTION_PRICES:
        logger.error(f"[CHECKOUT] Invalid subscription price ID: {price_id}")
        raise HTTPException(status_code=400, detail=f"Invalid subscription price ID: {price_id}")
    
    plan_info = SUBSCRIPTION_PRICES[price_id]
    
    # ========================================
    # 🔍 DEBUG: Log plan selection BEFORE Stripe call
    # ========================================
    logger.info("=" * 80)
    logger.info("[CHECKOUT] 📋 SUBSCRIPTION CHECKOUT REQUEST")
    logger.info(f"[CHECKOUT] User ID: {user_id}")
    logger.info(f"[CHECKOUT] User Email: {user_email}")
    logger.info(f"[CHECKOUT] Selected Plan: {plan_info['display_name']}")
    logger.info(f"[CHECKOUT] Price ID: {price_id}")
    logger.info(f"[CHECKOUT] Monthly Credits: {plan_info['monthly_credits']}")
    logger.info(f"[CHECKOUT] Mode: subscription")
    logger.info("=" * 80)
    
    try:
        logger.info(f"[CHECKOUT] 🚀 Calling StripeService.create_checkout_session()")
        
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            customer_email=user_email,  user_id=user_id,  # ← Link user immediately
            success_url=f"{settings.FRONTEND_URL}/dashboard?checkout=success",
            cancel_url=f"{settings.FRONTEND_URL}/pricing",
            mode="subscription",
        )
        
        logger.info(f"[CHECKOUT] ✅ 200 OK | Subscription session created | UserID: {user_id} | SessionID: {session.get('session_id')}")
        
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
    current_user=Depends(require_active_subscription),  # ← Subscription required
):
    """
    Credit pack checkout - Active subscription required.
    
    - Authentication AND subscription required
    - User must have active subscription to buy credit packs
    - Stripe mode: 'payment' (one-time)
    - Credits awarded via webhook
    """
    user_id = current_user["user_id"]
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
        
        # Construct URLs
        success_url = f"{settings.FRONTEND_URL}/dashboard?checkout=success"
        cancel_url = f"{settings.FRONTEND_URL}/dashboard?checkout=cancel"
        
        # 🔍 VERIFY: Log exact URLs that will be used
        logger.info(f"[CHECKOUT] 🔍 REDIRECT URLs:")
        logger.info(f"[CHECKOUT]   SUCCESS: {success_url}")
        logger.info(f"[CHECKOUT]   CANCEL:  {cancel_url}")
        logger.info(f"[CHECKOUT]   FRONTEND_URL: {settings.FRONTEND_URL}")
        
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            customer_email=user_email,
            user_id=user_id,
            success_url=success_url,
            cancel_url=cancel_url,
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
