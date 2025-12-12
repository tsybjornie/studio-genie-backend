import stripe
import logging
from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings
from app.billing.subscription_plans import get_plan_by_price_id

router = APIRouter()
logger = logging.getLogger("stripe-webhook")

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/billing/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook")

    # =========================
    # 1️⃣ Checkout completed
    # =========================
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        price_id = session["display_items"][0]["price"]["id"] if session.get("display_items") else None

        logger.info(f"Checkout completed for customer={customer_id}")

        if price_id:
            plan = get_plan_by_price_id(price_id)
            logger.info(f"Plan matched: {plan.display_name}")

            # TODO:
            # - create user if not exists
            # - assign subscription_id
            # - add plan.monthly_credits to user balance

    # =========================
    # 2️⃣ Subscription renewed
    # =========================
    if event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")

        logger.info(f"Invoice paid for subscription={subscription_id}")

        # TODO:
        # - find user by subscription_id
        # - ADD monthly credits again (rollover logic applies)

    return {"status": "ok"}
