from fastapi import FastAPI
from .auth import router as auth_router

def init_routes(app: FastAPI):
    # Auth
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
