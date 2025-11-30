from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # === Supabase ===
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "videos"

    # === JWT ===
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # === Stripe Keys ===
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # === Monthly Subscription Price IDs ===
    STRIPE_STARTER_PRICE_ID: str      # 60 credits
    STRIPE_CREATOR_PRICE_ID: str      # 150 credits
    STRIPE_PRO_PRICE_ID: str          # 360 credits

    # === One-Time Credit Packs ===
    STRIPE_CREDIT_PACK_30_PRICE_ID: str
    STRIPE_CREDIT_PACK_100_PRICE_ID: str
    STRIPE_CREDIT_PACK_300_PRICE_ID: str
    STRIPE_CREDIT_PACK_1000_PRICE_ID: str

    # === Coinbase ===
    COINBASE_API_KEY: str
    COINBASE_WEBHOOK_SECRET: str

    # === Redis / Celery ===
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # === App Settings ===
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    API_V1_PREFIX: str = "/api/v1"

    # === Credit System ===
    CREDITS_PER_VIDEO: int = 3
    TRIAL_VIDEOS: int = 1
    COINBASE_BONUS_PERCENT: int = 20

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
