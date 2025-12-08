from fastapi import FastAPI
from .auth import router as auth_router
from .billing import router as billing_router
from .billing_webhook import router as billing_webhook_router

def init_routes(app: FastAPI):
    # Auth
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    # Billing
    app.include_router(billing_router, prefix="/billing", tags=["Billing"])
    # Webhooks
    app.include_router(billing_webhook_router)  # Prefix is defined in the router itself

