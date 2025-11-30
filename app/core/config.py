from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "videos"
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # Stripe Price IDs
    STRIPE_STARTER_PRICE_ID: str
    STRIPE_CREATOR_PRICE_ID: str
    STRIPE_PRO_PRICE_ID: str
    STRIPE_CREDIT_PACK_20_PRICE_ID: str
    STRIPE_CREDIT_PACK_50_PRICE_ID: str
    STRIPE_CREDIT_PACK_120_PRICE_ID: str
    
    # Coinbase Commerce Configuration
    COINBASE_API_KEY: str
    COINBASE_WEBHOOK_SECRET: str
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Application Configuration
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    API_V1_PREFIX: str = "/api/v1"
    
    # Credit System Configuration
    CREDITS_PER_VIDEO: int = 3
    TRIAL_VIDEOS: int = 1
    COINBASE_BONUS_PERCENT: int = 20
    
    # Plan Credits
    STARTER_CREDITS: int = 20
    CREATOR_CREDITS: int = 50
    PRO_CREDITS: int = 120
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
