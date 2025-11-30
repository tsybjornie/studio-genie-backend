import logging
from datetime import datetime, timedelta
from app.core.database import db

logger = logging.getLogger(__name__)

class BillingService:

    # ADD CREDITS
    def add_credits(self, user_id: str, amount: int):
        try:
            user = (
                db.service_client.table("users")
                .select("credits_remaining")
                .eq("id", user_id)
                .single()
                .execute()
            )

            current = user.data.get("credits_remaining") or 0
            new_amount = current + amount

            db.service_client.table("users").update(
                {"credits_remaining": new_amount}
            ).eq("id", user_id).execute()

            logger.info(f"[CREDITS] Added {amount} → {user_id}")

        except Exception as e:
            logger.error(f"[CREDITS ERROR] {e}")

    # ACTIVATE SUBscription
    def activate_subscription(self, user_id: str, price_id: str):
        plan = self.map_plan(price_id)
        db.service_client.table("users").update({
            "plan": plan,
            "subscription_status": "active",
            "renewal_date": datetime.utcnow() + timedelta(days=30),
        }).eq("id", user_id).execute()

        logger.info(f"[SUBSCRIPTION] Activated {plan} for {user_id}")

    # CANCEL SUBscription
    def cancel_subscription(self, user_id: str):
        db.service_client.table("users").update({
            "plan": "free",
            "subscription_status": "canceled",
            "renewal_date": None,
        }).eq("id", user_id).execute()

        logger.info(f"[SUBSCRIPTION] Canceled for {user_id}")

    # MAP price → plan
    def map_plan(self, price_id: str) -> str:
        mapping = {
            "price_1SV4tkBBwifSvpdICrbo1QFJ": "starter",
            "price_1SV4uUBBwifSvpdIuoSpX0Q2": "creator",
            "price_1SV4vLBBwifSvpdIYZlLeYJ6": "pro",
        }
        return mapping.get(price_id, "unknown")

    # RENEWAl via EMAIL
    def apply_subscription_by_email(self, email: str, price_id: str):
        try:
            user = (
                db.service_client.table("users")
                .select("id")
                .eq("email", email)
                .single()
                .execute()
            )

            if user.data:
                self.activate_subscription(user.data["id"], price_id)
        except Exception as e:
            logger.error(f"[RENEWAL ERROR] {e}")


billing_service = BillingService()
