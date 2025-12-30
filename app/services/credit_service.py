from app.core.config import settings
from fastapi import HTTPException
from app.models.user import User
from app.models.subscription import Subscription
from app.core.subscription_prices import SUBSCRIPTION_PRICES
import logging

logger = logging.getLogger(__name__)

# ============================================
#   SUBSCRIPTION CREDIT AMOUNTS
#   Derived from canonical subscription prices
# ============================================

# Build credit map from canonical subscription prices
SUBSCRIPTION_CREDIT_MAP = {
    price_id: info["monthly_credits"]
    for price_id, info in SUBSCRIPTION_PRICES.items()
}

# ============================================
#   CREDIT PACKS (ONE-TIME PURCHASES)
#   Single Source of Truth for Stripe Price -> Credits
# ============================================

PRICE_ID_TO_CREDITS = {
    "price_1SdZ50BBwifSvpdIWW1Ntt22": 9,    # Small - $25
    "price_1SdZ7TBBwifSvpdIAZqbTuLR": 30,   # Medium - $65
    "price_1SdZ7xBBwifSvpdI1B6BjybU": 90,   # Power - $119
}


class CreditService:

    # -------------------------
    # Dashboard credit retrieval
    # -------------------------
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

    # -------------------------------------------
    # Award credits after Stripe subscription paid
    # -------------------------------------------
    def apply_subscription_credits(self, user_id: str, price_id: str):
        # Skip auto-credit logic in test mode
        if settings.TEST_MODE:
            logger.info(f"[TEST MODE] Skipping subscription credit auto-application for user {user_id}")
            return False
            
        user = User.get(user_id)
        if not user:
            raise Exception("User not found")

        credits_to_add = SUBSCRIPTION_CREDIT_MAP.get(price_id)
        if credits_to_add is None:
            logger.warning(f"[CREDITS] Unknown Stripe price_id={price_id}")
            return False

        user.credits += credits_to_add
        user.save()

        logger.info(f"[CREDITS] +{credits_to_add} credited to {user.email}")
        return True

    # -----------------------------------
    # Apply one-time purchased credit pack
    # -----------------------------------
    def apply_credit_pack(self, user_id: str, price_id: str):
        """Apply credits from a one-time credit pack purchase.
        
        Args:
            user_id: User ID to credit
            price_id: Stripe price ID from webhook (cryptographically verified)
        """
        user = User.get(user_id)
        if not user:
            raise Exception("User not found")

        credits = PRICE_ID_TO_CREDITS.get(price_id)
        if credits is None:
            logger.warning(f"[CREDIT PACK] Unknown price_id={price_id}")
            return False

        user.credits += credits
        user.save()

        logger.info(f"[CREDIT PACK] +{credits} credits added to {user.email}")
        return True

    # --------------
    # One-time trial use (3 credits = 1 video)
    # --------------
    def apply_trial(self, user_id: str):
        # Skip auto-credit logic in test mode
        if settings.TEST_MODE:
            logger.info(f"[TEST MODE] Skipping trial credit auto-application for user {user_id}")
            return False
            
        user = User.get(user_id)
        if not user:
            raise Exception("User not found")

        # User already claimed
        if user.has_trial_used:
            logger.warning(f"[TRIAL] User {user.email} already used trial.")
            return False

        # Grant trial
        trial_credits = 3
        user.credits += trial_credits
        user.has_trial_used = True
        user.save()

        logger.info(f"[TRIAL] Granted {trial_credits} trial credits to {user.email}")
        return True


# Global instance used by all routes
credit_service = CreditService()
