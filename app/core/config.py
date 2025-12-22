import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ==============================
    # CORE APP SETTINGS
    # ==============================
    ENVIRONMENT: str = "production"
    APP_URL: str = "http://localhost:3000"
    FRONTEND_URL: str = "https://studio-genie-frontend-lua0ipmge-chamoreio.vercel.app"
    
    # ==============================
    # TESTING
    # ==============================
    TEST_MODE: bool = False  # Set to True to disable auto-credit logic

    # ==============================
    # DATABASE (POSTGRESQL)
    # ==============================
    DATABASE_URL: str

    # ==============================
    # JWT CONFIG
    # ==============================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

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
          - Single: "https://a.com"
          - Multiple: "https://a.com,https://b.com"
          - Wildcard: "*"
        """
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
