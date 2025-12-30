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
        "https://studio-genie-frontend.vercel.app",
        "https://studio-genie-frontend-cx27plzvs-chamoreio.vercel.app",
        "https://studio-genie-frontend-bztzhulle-chamoreio.vercel.app",
        "https://studio-genie-frontend-4rxnzkek6-chamoreio.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000"
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
    """Application startup"""
    logger.info("🚀 Starting Studio Génie API…")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # =========================================================
    # STRIPE CONFIGURATION VALIDATION
    # =========================================================
    try:
        from app.services.stripe_validator import validate_stripe_configuration
        logger.info("Running Stripe configuration validation...")
        validate_stripe_configuration()
    except RuntimeError as e:
        logger.error(f"❌ STARTUP FAILED: {str(e)}")
        logger.error("Application cannot start with invalid Stripe configuration")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during Stripe validation: {str(e)}")
        raise
    
    # 🔍 DEBUG: Print all registered routes
    logger.info("=" * 60)
    logger.info("REGISTERED ROUTES:")
    logger.info("=" * 60)
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ','.join(route.methods) if route.methods else 'N/A'
            logger.info(f"{methods:10} {route.path}")
    logger.info("=" * 60)

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
