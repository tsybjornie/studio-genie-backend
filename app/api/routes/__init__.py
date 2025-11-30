from fastapi import APIRouter

from .auth import router as auth_router
from .credits import router as credits_router
from .videos import router as videos_router
from .billing import router as billing_router
from .subscriptions import router as subscriptions_router

# NEW: usage engine
from .usage import router as usage_router

# WEBHOOKS
from .webhook_stripe import router as stripe_webhook_router
from .webhook_coinbase import router as coinbase_webhook_router


def init_routes(app):

    # --------------------------
    # MAIN API (protected routes)
    # --------------------------
    api_router = APIRouter(prefix="/api/v1")

    # Auth, users
    api_router.include_router(auth_router)

    # Credits system
    api_router.include_router(credits_router)

    # Video generation (Studio Genie)
    api_router.include_router(videos_router)

    # Hybrid billing engine (Stripe + Coinbase)
    api_router.include_router(billing_router)

    # Subscription management UI/API
    api_router.include_router(subscriptions_router)

    # NEW: Usage deduction & balance API
    api_router.include_router(usage_router)

    # Attach to app
    app.include_router(api_router)

    # --------------------------
    # WEBHOOKS (unprotected)
    # --------------------------
    # Stripe webhook → /webhooks/stripe
    app.include_router(stripe_webhook_router, prefix="/webhooks")

    # Coinbase webhook → /webhooks/coinbase
    app.include_router(coinbase_webhook_router, prefix="/webhooks")
