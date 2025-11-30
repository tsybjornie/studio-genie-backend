import stripe
import logging
from fastapi import HTTPException
from app.core.config import settings
from app.services.billing_service import billing_service

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


STRIPE_PRICE_SUBSCRIPTIONS = {
    "starter": "price_1SV4tkBBwifSvpdICrbo1QFJ",
    "creator": "price_1SV4uUBBwifSvpdIuoSpX0Q2",
    "pro":     "price_1SV4vLBBwifSvpdIYZlLeYJ6",
}

STRIPE_PRICE_CREDIT_PACKS = {
    "30":   "price_1SWew0BBwifSvpdIushlBKMf",
    "100":  "price_1SWewfBBwifSvpdIplolWgJo",
    "300":  "price_1SWexdBBwifSvpdIqtX4C8uT",
    "1000": "price_1SWf2EBBwifSvpdILOY6TB9U",
}

CREDIT_PACK_AMOUNTS = {
    "30": 30,
    "100": 100,
    "300": 300,
    "1000": 1000,
}


class StripeService:
    # CREATE CHECKOUT SESSION
    def create_checkout_session(self, price_id, customer_email, user_id, success_url, cancel_url, mode):
        try:
            session = stripe.checkout.Session.create(
                mode=mode,
                customer_email=customer_email,
                client_reference_id=user_id,
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                expand=["line_items"],
            )

            return {"session_id": session.id, "url": session.url}

        except Exception as e:
            logger.error(f"[STRIPE] Checkout session error: {e}")
            raise HTTPException(500, "Stripe checkout failed")

    # VALIDATE WEBHOOK SIGNATURE
    def construct_webhook_event(self, payload, signature):
        try:
            return stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except Exception:
            raise HTTPException(400, "Invalid Stripe webhook signature")

    # CHECKOUT COMPLETED
    def handle_checkout_completed(self, session):
        user_id = session.get("client_reference_id")

        try:
            price_id = session["line_items"]["data"][0]["price"]["id"]
        except:
            logger.error("[STRIPE] Missing line_items")
            return

        # Subscription
        if price_id in STRIPE_PRICE_SUBSCRIPTIONS.values():
            billing_service.activate_subscription(user_id, price_id)
            return

        # Credit Pack
        for pack, pid in STRIPE_PRICE_CREDIT_PACKS.items():
            if price_id == pid:
                billing_service.add_credits(user_id, CREDIT_PACK_AMOUNTS[pack])
                return

    # RENEWAL
    def handle_subscription_renewal(self, invoice):
        try:
            price_id = invoice["lines"]["data"][0]["price"]["id"]
        except:
            return

        customer_email = invoice.get("customer_email")

        billing_service.apply_subscription_by_email(customer_email, price_id)


stripe_service = StripeService()
