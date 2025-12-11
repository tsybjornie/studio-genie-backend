from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import init_routes
from app.utils.logger import logger

# =========================================================
# FastAPI App
# =========================================================

app = FastAPI(
    title="Studio Génie API",
    description="UGC AI Video SaaS Backend - Brainwash Labs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://studio-genie-frontend.vercel.app",
        "https://studio-genie-frontend-5j436leom-chamoreio.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# STARTUP (CLEAN + SAFE)
# =========================================================

@app.on_event("startup")
async def startup_event():
    """MGX startup"""
    logger.info("🚀 Starting Studio Génie API…")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # No database table creation (Supabase is schema-first)
    logger.info("Supabase client initialized.")

# =========================================================
# SHUTDOWN
# =========================================================

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Studio Génie API…")

# =========================================================
# HEALTHCHECK
# =========================================================

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Studio Génie API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# =========================================================
# ROUTES (AUTH, BILLING, COINBASE, VIDEOS, ETC.)
# =========================================================

init_routes(app)

# =========================================================
# GLOBAL EXCEPTION HANDLER
# =========================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {"detail": "Internal server error."}

# =========================================================
# LOCAL UVICORN RUNNER (DEV ONLY)
# =========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
