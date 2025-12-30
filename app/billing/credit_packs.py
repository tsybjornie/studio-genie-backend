"""
Credit Packs Configuration
Defines one-time credit purchase options with pricing.
"""

from typing import Dict, Any


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
    "small": CreditPack(
        key="small",
        display_name="Small Pack",
        stripe_price_id="price_1SdZ50BBwifSvpdIWW1Ntt22",  # Your Stripe price ID for small
        credits=25,  # $25 / 3 credits per video ≈ 8 videos, but we'll give 25 credits
        price_usd=25.00,
        popular=False
    ),
    "medium": CreditPack(
        key="medium",
        display_name="Medium Pack",
        stripe_price_id="price_1SdZ7TBBwifSvpdIAZqbTuLR",  # Your Stripe price ID for medium
        credits=75,  # $65 ≈ 21-25 videos worth of credits
        price_usd=65.00,
        popular=True
    ),
    "power": CreditPack(
        key="power",
        display_name="Power Pack",
        stripe_price_id="price_1SdZ7xBBwifSvpdI1B6BjybU",  # Your Stripe price ID for pro/power
        credits=150,  # $119 ≈ 40-50 videos worth of credits
        price_usd=119.00,
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
