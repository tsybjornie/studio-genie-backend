from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription


# ============================================
#   SUBSCRIPTION CREDIT AMOUNTS (US MARKET)
# ============================================
# 3 credits = 1 video
# Starter  ($39)  → 60 credits  (~20 videos)
# Creator  ($79)  → 150 credits (~50 videos)
# Pro      ($149) → 360 credits (~120 videos)

SUBSCRIPTION_CREDIT_MAP = {
    settings.STRIPE_STARTER_PRICE_ID: 60,
    settings.STRIPE_CREATOR_PRICE_ID: 150,
    settings.STRIPE_PRO_PRICE_ID: 360,
}


# ============================================
#   OPTIONAL CREDIT PACKS (ONE-TIME BUY)
# ============================================

CREDIT_PACK_AMOUNTS = {
    "30": {"credits": 30, "price_usd": 12},
    "100": {"credits": 100, "price_usd": 35},
    "300": {"credits": 300, "price_usd": 90},
    "1000": {"credits": 1000, "price_usd": 250},
}


# ============================================
#   MAIN CREDIT SERVICE
# ============================================

class CreditService:

    # -------------------------------
    # Dashboard credit snapshot
    # -------------------------------
    def get_user_credits(self, user_id: str):
        user = User.get(user_id)
        if not user:
            raise Exception("User not found")

        subscription = Subscription.get_by_user_id(user_id)

        return {
            "credits_remaining": user.credits,
            "has_trial_used": user.has_trial_used,
            "plan": subscription.plan if subscription else None,
        }

    # -------------------------------
    # Subscription → credit awarding
    # Called from Stripe webhook
    # -------------------------------
    def apply_subscription_credits(self, user_id: str, price_id: str):
        user = User.get(user_id)
        if not user:
            raise Exception("User not found")

        credits_to_add = SUBSCRIPTION_CREDIT_MAP.get(price_id)

        if credits_to_add is None:
            print(f"[CREDITS] Unknown Stripe price_id={price_id} — no rule found.")
            return False

        user.credits += credits_to_add
        user.save()

        print(f"[CREDITS] +{credits_to_add} credits awarded to {user.email}")
        return True

    # -------------------------------
    # One-time pack purchase
    # -------------------------------
    def apply_credit_pack(self, user_id: str, pack_key: str):
        user = User.get(user_id)
        if not user:
            raise Exception("User not found")

        if pack_key not in CREDIT_PACK_AMOUNTS:
            raise Exception("Invalid credit pack")

        amount = CREDIT_PACK_AMOUNTS[pack_key]["credits"]

        user.credits += amount
        user.save()

        print(f"[CREDIT PACK] +{amount} credits added to {user.email}")
        return True

    # -------------------------------
    # ONE-TIME TRIAL (3 credits = 1 video)
    # -------------------------------
    def apply_trial(self, user_id: str):
        user = User.get(user_id)
        if not user:
            raise Exception("User not found")

        # User already claimed
        if user.has_trial_used:
            print(f"[TRIAL] User {user.email} already used trial.")
            return False

        # Grant trial
        trial_credits = 3   # 1 video
        user.credits += trial_credits
        user.has_trial_used = True
        user.save()

        print(f"[TRIAL] Granted 3 trial credits to {user.email}")
        return True


# Global instance imported elsewhere
credit_service = CreditService()
