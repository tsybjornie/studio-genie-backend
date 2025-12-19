import logging
import stripe
from app.core.config import settings
from datetime import datetime, timedelta
from app.core.database import get_connection

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class BillingService:

    # ADD CREDITS
    def add_credits(self, user_id: str, amount: int):
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            # Get current credits
            cur.execute(
                "SELECT credits FROM users WHERE id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            
            if not result:
                cur.close()
                conn.close()
                logger.error(f"[CREDITS ERROR] User {user_id} not found")
                return
            
            current = result["credits"] or 0
            new_amount = current + amount
            
            # Update credits
            cur.execute(
                "UPDATE users SET credits = %s WHERE id = %s",
                (new_amount, user_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"[CREDITS] Added {amount} → {user_id}")

        except Exception as e:
            logger.error(f"[CREDITS ERROR] {e}")

    # ACTIVATE SUBscription
    def activate_subscription(self, user_id: str, price_id: str):
        try:
            plan = self.map_plan(price_id)
            renewal_date = datetime.utcnow() + timedelta(days=30)
            
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                UPDATE users 
                SET plan = %s, 
                    subscription_status = %s, 
                    renewal_date = %s
                WHERE id = %s
                """,
                (plan, "active", renewal_date, user_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"[SUBSCRIPTION] Activated {plan} for {user_id}")
        except Exception as e:
            logger.error(f"[SUBSCRIPTION ERROR] {e}")

    # CANCEL SUBscription
    def cancel_subscription(self, user_id: str):
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                UPDATE users 
                SET plan = %s, 
                    subscription_status = %s, 
                    renewal_date = NULL
                WHERE id = %s
                """,
                ("free", "canceled", user_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"[SUBSCRIPTION] Canceled for {user_id}")
        except Exception as e:
            logger.error(f"[SUBSCRIPTION ERROR] {e}")

    # MAP price → plan
    def map_plan(self, price_id: str) -> str:
        mapping = {
            settings.STRIPE_STARTER_PRICE_ID: "starter",
            settings.STRIPE_CREATOR_PRICE_ID: "creator",
            settings.STRIPE_PRO_PRICE_ID: "pro",
        }
        return mapping.get(price_id, "unknown")

    # RENEWAl via EMAIL
    def apply_subscription_by_email(self, email: str, price_id: str):
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                self.activate_subscription(user["id"], price_id)
        except Exception as e:
            logger.error(f"[RENEWAL ERROR] {e}")


    # CREATE CHECKOUT SESSION
    async def create_session(self, price_id: str):
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=f"{settings.APP_URL}/dashboard?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.APP_URL}/pricing?cancelled=true",
            )
            return session.url
        except Exception as e:
            logger.error(f"[STRIPE ERROR] {e}")
            raise e


billing_service = BillingService()
