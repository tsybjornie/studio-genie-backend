from fastapi import FastAPI

from .routes.auth import router as auth_router
from .routes.billing import router as billing_router
from .routes.credits import router as credits_router
from .routes.subscriptions import router as subscriptions_router
from .routes.videos import router as videos_router
from .routes.coinbase import router as coinbase_router

def init_routes(app: FastAPI):
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.include_router(billing_router, prefix="/api/v1/billing")
    app.include_router(credits_router, prefix="/api/v1/credits")
    app.include_router(subscriptions_router, prefix="/api/v1/subscriptions")
    app.include_router(videos_router, prefix="/api/v1/videos")
    app.include_router(coinbase_router, prefix="/api/v1/coinbase")
