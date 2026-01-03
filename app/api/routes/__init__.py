from fastapi import FastAPI
from .auth import router as auth_router
from .billing import router as billing_router
from .billing_webhook import router as billing_webhook_router
from .subscription_change import router as subscription_change_router
from .options import router as options_router
from .users import router as users_router
from .videos import router as videos_router
from .video import router as video_router
from .me import router as me_router
from .admin import router as admin_router
from .stripe_routes import router as stripe_routes_router
from .webhook_stripe import router as webhook_stripe_router

def init_routes(app: FastAPI):
    # Global OPTIONS handler (must be first)
    app.include_router(options_router)
    # Auth
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    # Me (combined dashboard endpoint)
    app.include_router(me_router, prefix="/me", tags=["Me"])
    # Users
    app.include_router(users_router, prefix="/users", tags=["Users"])
    # Videos
    app.include_router(videos_router, prefix="/videos", tags=["Videos"])
    # Video Generation
    app.include_router(video_router, tags=["Video"])
    # Stripe Checkout (Canonical v1.0) - router already has prefix="/api/stripe"
    app.include_router(stripe_routes_router)  # ✅ FIXED: Don't override tags, use router's own
    # Billing (Legacy - consider deprecating)
    app.include_router(billing_router, prefix="/billing", tags=["Billing"])
    # Webhooks
    app.include_router(webhook_stripe_router, tags=["Stripe Webhooks"])  # Canonical v1.0 - router has its own prefix
    app.include_router(billing_webhook_router)  # Legacy
    # Subscription Change
    app.include_router(subscription_change_router)
    # Admin (testing only)
    app.include_router(admin_router)
