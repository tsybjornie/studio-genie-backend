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
    # Billing
    app.include_router(billing_router, prefix="/billing", tags=["Billing"])
    # Webhooks
    app.include_router(billing_webhook_router)  # 🔥 REQUIRED
    # Subscription Change
    app.include_router(subscription_change_router)


