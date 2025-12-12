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
#  SUBSCRIPTION PLANS - Match Frontend Pricing
# ---------------------------------------------------

SUBSCRIPTION_PLANS = {
    "starter": SubscriptionPlan(
        name="starter",
        display_name="Starter",
        price_id=settings.STRIPE_STARTER_PRICE_ID,
        monthly_credits=4,  # 4 AI-generated videos
        price_usd=39.00,  # $39/mo
        features=[
            "4 AI-generated videos",
            "300+ AI creators",
            "35+ languages",
            "2-minute rendering",
            "Sora 2",
            "Bulk content generator",
            "B-roll generator"
        ]
    ),
    "creator": SubscriptionPlan(
        name="creator",
        display_name="Creator",
        price_id=settings.STRIPE_CREATOR_PRICE_ID,
        monthly_credits=12,  # 12 AI-generated videos
        price_usd=79.00,  # $79/mo
        features=[
            "12 AI-generated videos",
            "300+ AI creators",
            "35+ languages",
            "2-minute rendering",
            "Sora 2",
            "Bulk content generator",
            "B-roll generator"
        ]
    ),
    "pro": SubscriptionPlan(
        name="pro",
        display_name="Pro",
        price_id=settings.STRIPE_PRO_PRICE_ID,
        monthly_credits=30,  # 30 AI-generated videos
        price_usd=149.00,  # $149/mo
        features=[
            "30 AI-generated videos",
            "300+ AI creators",
            "35+ languages",
            "2-minute rendering",
            "Sora 2",
            "Bulk content generator",
            "B-roll generator",
            "Product-in-hand",
            "Video Agent"
        ]
    ),
    "custom": SubscriptionPlan(
        name="custom",
        display_name="Custom",
        price_id="",  # No Stripe price ID - custom pricing
        monthly_credits=0,  # Negotiated per customer
        price_usd=0.0,  # Custom pricing
        features=[
            "50–500 videos",
            "Everything in Pro",
            "API access",
            "Dedicated manager",
            "Team seats",
            "24/7 support"
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
