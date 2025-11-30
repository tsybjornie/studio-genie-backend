"""
Credit Packs Configuration
Defines one-time credit purchase options with pricing.
"""

from typing import Dict, Any
from app.core.config import settings


class CreditPack:
    """Represents a one-time credit purchase pack."""

    def __init__(
        self,
        key: str,
        display_name: str,
        stripe_price_id: str,
        credits: int,
        price_usd: float,
        popular: bool = False
    ):
        self.key = key
        self.display_name = display_name
        self.stripe_price_id = stripe_price_id
        self.credits = credits
        self.price_usd = price_usd
        self.popular = popular

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "stripe_price_id": self.stripe_price_id,
            "credits": self.credits,
            "price_usd": self.price_usd,
            "price_per_credit": round(self.price_usd / self.credits, 2),
            "popular": self.popular
        }


# ---------------------------------------------------
#  🔥 REAL CREDIT PACKS FROM STRIPE + YOUR PRICING
# ---------------------------------------------------

CREDIT_PACKS = {
    "30": CreditPack(
        key="30",
        display_name="30 Credits Pack",
        stripe_price_id=settings.STRIPE_CREDIT_PACK_30_PRICE_ID,
        credits=30,
        price_usd=9,
        popular=False
    ),
    "100": CreditPack(
        key="100",
        display_name="100 Credits Pack",
        stripe_price_id=settings.STRIPE_CREDIT_PACK_100_PRICE_ID,
        credits=100,
        price_usd=29,
        popular=True
    ),
    "300": CreditPack(
        key="300",
        display_name="300 Credits Pack",
        stripe_price_id=settings.STRIPE_CREDIT_PACK_300_PRICE_ID,
        credits=300,
        price_usd=79,
        popular=False
    ),
    "1000": CreditPack(
        key="1000",
        display_name="1000 Credits Pack",
        stripe_price_id=settings.STRIPE_CREDIT_PACK_1000_PRICE_ID,
        credits=1000,
        price_usd=249,
        popular=False
    ),
}


def get_pack_by_key(pack_key: str) -> CreditPack:
    pack = CREDIT_PACKS.get(pack_key)
    if not pack:
        raise ValueError(f"Unknown credit pack: {pack_key}")
    return pack


def get_pack_by_price_id(price_id: str) -> CreditPack:
    for pack in CREDIT_PACKS.values():
        if pack.stripe_price_id == price_id:
            return pack
    raise ValueError(f"Unknown Stripe price ID: {price_id}")


def get_all_packs() -> list[CreditPack]:
    return list(CREDIT_PACKS.values())
