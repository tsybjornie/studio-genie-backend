from app.core.config import settings

# Mapping Stripe subscription price IDs → credit amounts
SUBSCRIPTION_CREDIT_MAP = {
    settings.STRIPE_STARTER_PRICE_ID: 60,   # Starter plan = 60 credits
    settings.STRIPE_CREATOR_PRICE_ID: 150,  # Creator plan = 150 credits
    settings.STRIPE_PRO_PRICE_ID: 360,      # Pro plan = 360 credits
}

def apply_credits(user, price_id):
    """
    Award credits to user after Stripe invoice.paid webhook.
    """
    credits_to_add = SUBSCRIPTION_CREDIT_MAP.get(price_id)

    if credits_to_add is None:
        print(f"[WARN] No credit rule for price_id={price_id}")
        return False

    user.credits += credits_to_add
    user.save()

    print(f"[CREDITS] Added {credits_to_add} credits to user {user.email}")
    return True
