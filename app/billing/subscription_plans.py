"""
Subscription Plans Configuration
Defines all available subscription tiers with their pricing and credit allocations.
"""

from typing import Dict, Any
from app.core.config import settings


class SubscriptionPlan:
    """Represents a subscription plan with its details."""

    def __init__(
        self,
        name: str,
        display_name: str,
        price_id: str,
        monthly_credits: int,
        price_usd: float,
        features: list[str]
    ):
        self.name = name
        self.display_name = display_name
        self.price_id = price_id
        self.monthly_credits = monthly_credits
        self.price_usd = price_usd
        self.features = features

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "price_id": self.price_id,
            "monthly_credits": self.monthly_credits,
            "price_usd": self.price_usd,
            "features": self.features
        }


# ---------------------------------------------------
#  🔥 REAL PRICING FROM YOUR WEBSITE + STRIPE
# ---------------------------------------------------

SUBSCRIPTION_PLANS = {
    "starter": SubscriptionPlan(
        name="starter",
        display_name="Starter",
        price_id=settings.STRIPE_STARTER_PRICE_ID,
        monthly_credits=60,          # 60 credits total
        price_usd=29.00,             # $29
        features=[
            "20 AI-generated videos per month",
            "60 credits total",
            "HD video generation",
            "Basic templates",
            "Standard processing",
            "Email support"
        ]
    ),
    "creator": SubscriptionPlan(
        name="creator",
        display_name="Creator",
        price_id=settings.STRIPE_CREATOR_PRICE_ID,
        monthly_credits=150,         # 150 credits total
        price_usd=59.00,             # $59
        features=[
            "50 AI-generated videos per month",
            "150 credits total",
            "HD + 4K video generation",
            "Premium templates",
            "Faster processing",
            "Priority support"
        ]
    ),
    "pro": SubscriptionPlan(
        name="pro",
        display_name="Pro",
        price_id=settings.STRIPE_PRO_PRICE_ID,
        monthly_credits=360,         # 360 credits total
        price_usd=99.00,             # $99
        features=[
            "120 AI-generated videos per month",
            "360 credits total",
            "Fastest processing",
            "All premium templates",
            "API access",
            "Team features",
            "24/7 priority support"
        ]
    ),
}


# Helper functions

def get_plan_by_name(plan_name: str) -> SubscriptionPlan:
    plan = SUBSCRIPTION_PLANS.get(plan_name.lower())
    if not plan:
        raise ValueError(f"Unknown subscription plan: {plan_name}")
    return plan


def get_plan_by_price_id(price_id: str) -> SubscriptionPlan:
    for plan in SUBSCRIPTION_PLANS.values():
        if plan.price_id == price_id:
            return plan
    raise ValueError(f"Unknown Stripe price ID: {price_id}")


def get_all_plans() -> list[SubscriptionPlan]:
    return list(SUBSCRIPTION_PLANS.values())
