from pydantic import BaseModel, Field
from typing import Optional, Dict


# ============================================================
# STRIPE — CHECKOUT SESSION (SUBSCRIPTIONS + CREDIT PACKS)
# ============================================================

class CheckoutSessionRequest(BaseModel):
    """
    Schema for creating a Stripe checkout session.
    Works for both:
    - Subscription plans (mode='subscription')
    - One-time credit packs (mode='payment')
    """
    price_id: str = Field(..., description="Stripe Price ID")
    success_url: str = Field(..., description="Success redirect URL")
    cancel_url: str = Field(..., description="Cancel redirect URL")
    mode: str = Field(..., description="subscription | payment")


class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str


# ============================================================
# COINBASE — CREDIT PACK PURCHASES
# ============================================================

class CoinbaseLinkRequest(BaseModel):
    """
    Request to create a Coinbase Commerce checkout link
    using an internal pack key like:
    - starter
    - creator
    - pro
    - credits_30
    - credits_100
    - credits_300
    - credits_1000
    """
    pack_key: str = Field(..., description="Internal credit pack key")
    success_url: str
    cancel_url: str


class CoinbaseLinkResponse(BaseModel):
    hosted_url: str
    charge_id: str
    amount_usd: float
    credits: int


# ============================================================
# BILLING PORTAL (Stripe)
# ============================================================

class PortalSessionResponse(BaseModel):
    url: str


# ============================================================
# GENERIC WEBHOOK EVENT (optional)
# ============================================================

class WebhookEvent(BaseModel):
    type: str
    data: Dict
