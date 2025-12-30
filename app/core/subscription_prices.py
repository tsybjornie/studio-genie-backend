"""
Canonical Subscription Prices - Single Source of Truth

This module defines the ONLY source of truth for subscription price IDs.
All other modules must import from here.

DO NOT create duplicate price maps elsewhere!
"""

# =============================================================================
# LIVE MODE RECURRING MONTHLY SUBSCRIPTION PRICES
# Single source of truth - import this everywhere
# =============================================================================

SUBSCRIPTION_PRICES = {
    "price_1SjjxCBBwifSvpdI963oyLLB": {
        "plan_name": "starter",
        "display_name": "Starter",
        "monthly_credits": 60,
        "price_usd": 39,
    },
    "price_1SjjxfBBwifSvpdIeWCEYEQY": {
        "plan_name": "creator",
        "display_name": "Creator",
        "monthly_credits": 150,
        "price_usd": 79,
    },
    "price_1Sjjy4BBwifSvpdIIJxsl1yz": {
        "plan_name": "pro",
        "display_name": "Pro",
        "monthly_credits": 360,
        "price_usd": 149,
    },
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_price_id(plan_name: str) -> str:
    """
    Get price ID by plan name.
    
    Args:
        plan_name: Plan name ("starter", "creator", or "pro")
        
    Returns:
        str: Stripe price ID
        
    Raises:
        ValueError: If plan name is not found
    """
    for price_id, info in SUBSCRIPTION_PRICES.items():
        if info["plan_name"] == plan_name:
            return price_id
    raise ValueError(f"Unknown subscription plan: {plan_name}")


def get_plan_info(price_id: str) -> dict:
    """
    Get plan information by price ID.
    
    Args:
        price_id: Stripe price ID
        
    Returns:
        dict: Plan information (plan_name, display_name, monthly_credits, price_usd)
        
    Raises:
        ValueError: If price ID is not found
    """
    if price_id not in SUBSCRIPTION_PRICES:
        raise ValueError(f"Unknown subscription price ID: {price_id}")
    return SUBSCRIPTION_PRICES[price_id]


def is_subscription_price(price_id: str) -> bool:
    """Check if a price ID is a subscription price."""
    return price_id in SUBSCRIPTION_PRICES


def get_all_price_ids() -> list:
    """Get list of all subscription price IDs."""
    return list(SUBSCRIPTION_PRICES.keys())


def get_all_plan_names() -> list:
    """Get list of all plan names."""
    return [info["plan_name"] for info in SUBSCRIPTION_PRICES.values()]
