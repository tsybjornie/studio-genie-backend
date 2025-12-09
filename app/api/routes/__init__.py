from fastapi import FastAPI
from .auth import router as auth_router
from .billing import router as billing_router
from .billing_webhook import router as billing_webhook_router
from .subscription_change import router as subscription_change_router

def init_routes(app: FastAPI):
    # Auth
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    # Billing
    app.include_router(billing_router, prefix="/billing", tags=["Billing"])
    # Webhooks
    app.include_router(billing_webhook_router)  # 🔥 REQUIRED
    # Subscription Change
    app.include_router(subscription_change_router)


