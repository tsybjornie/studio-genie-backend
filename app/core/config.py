import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ==============================
    # CORE APP SETTINGS
    # ==============================
    ENVIRONMENT: str = "production"
    SECRET_KEY: str
    APP_URL: str = "http://localhost:3000"

    # ==============================
    # DATABASE (POSTGRESQL)
    # ==============================
    DATABASE_URL: str

    # ==============================
    # JWT CONFIG
    # ==============================
    JWT_SECRET: str
    JWT_EXPIRES_IN: str = "7d"
    JWT_ALGORITHM: str = "HS256"

    # ==============================
    # STRIPE CONFIG
    # ==============================
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    STRIPE_STARTER_PRICE_ID: str
    STRIPE_CREATOR_PRICE_ID: str
    STRIPE_PRO_PRICE_ID: str

    STRIPE_CREDIT_PACK_30_PRICE_ID: str | None = None
    STRIPE_CREDIT_PACK_100_PRICE_ID: str | None = None
    STRIPE_CREDIT_PACK_300_PRICE_ID: str | None = None
    STRIPE_CREDIT_PACK_1000_PRICE_ID: str | None = None

    # ==============================
    # CORS
    # ==============================
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self):
        """
        Required by FastAPI middleware.
        Converts CSV string → Python list.
        Works for:
            "*" 
            "http://localhost:3000"
            "http://a.com, http://b.com"
        """
        if self.CORS_ORIGINS == "*" or self.CORS_ORIGINS.strip() == "":
            return ["*"]

        # split comma-separated values
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
