from fastapi import APIRouter, HTTPException, Depends, Request, Header
import logging
import json

from app.schemas.billing_schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CoinbaseLinkRequest,
    CoinbaseLinkResponse,
)
from app.core.security import get_current_user
from app.services.stripe_service import stripe_service
from app.services.coinbase_service import coinbase_service
from app.services.billing_service import billing_service
from app.core.database import db

router = APIRouter(prefix="/billing", tags=["Billing"])
logger = logging.getLogger(__name__)


# =========================================================
# STRIPE CHECKOUT — Subscriptions & Credit Packs
# =========================================================
@router.post("/create_checkout_session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        session = stripe_service.create_checkout_session(
            price_id=request.price_id,
            customer_email=current_user["email"],
            user_id=current_user["id"],
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            mode=request.mode,
        )

        return CheckoutSessionResponse(
            session_id=session["session_id"],
            url=session["url"],
        )

    except Exception as e:
        logger.error(f"[STRIPE CREATE SESSION ERROR] {e}")
        raise HTTPException(500, "Failed to create Stripe checkout session")


# =========================================================
# COINBASE CREDIT PACK LINK
# =========================================================
@router.post("/coinbase/link", response_model=CoinbaseLinkResponse)
async def coinbase_link(
    request: CoinbaseLinkRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        hosted_url = coinbase_service.generate_checkout_link(
            pack_key=request.pack_key,
            user_id=current_user["id"],
        )

        return CoinbaseLinkResponse(hosted_url=hosted_url)

    except Exception as e:
        logger.error(f"[COINBASE LINK ERROR] {e}")
        raise HTTPException(500, "Failed to generate Coinbase link")


# =========================================================
# STRIPE WEBHOOK (NO AUTH)
# =========================================================
@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe_service.construct_webhook_event(payload, sig)
    except Exception as e:
        logger.error(f"[STRIPE WEBHOOK] Signature error: {e}")
        raise HTTPException(400, "Invalid Stripe signature")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"[STRIPE WEBHOOK] EVENT = {event_type}")

    # -------------------------
    # 1️⃣ Payment Completed
    # -------------------------
    if event_type == "checkout.session.completed":
        stripe_service.handle_checkout_completed(data)
        return {"status": "ok"}

    # -------------------------
    # 2️⃣ Subscription Renewal
    # -------------------------
    if event_type == "invoice.payment_succeeded":
        stripe_service.handle_subscription_renewal(data)
        return {"status": "ok"}

    # -------------------------
    # 3️⃣ Subscription Canceled
    # -------------------------
    if event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")

        try:
            user = (
                db.service_client.table("users")
                .select("id")
                .eq("stripe_customer_id", customer_id)
                .single()
                .execute()
            )
            if user.data:
                billing_service.cancel_subscription(user.data["id"])
        except Exception as e:
            logger.error(f"[CANCEL ERROR] {e}")

        return {"status": "ok"}

    return {"status": "ignored"}


# =========================================================
# COINBASE WEBHOOK
# =========================================================
@router.post("/webhook/coinbase")
async def coinbase_webhook(request: Request, x_cc_webhook_signature: str = Header(None)):
    raw = await request.body()

    if not coinbase_service.verify_signature(raw, x_cc_webhook_signature):
        raise HTTPException(400, "Invalid Coinbase signature")

    payload = json.loads(raw)
    event_type = payload["event"]["type"]

    logger.info(f"[COINBASE WEBHOOK] {event_type}")

    if event_type == "charge:confirmed":
        metadata = payload["event"]["data"]["metadata"]
        user_id = metadata["user_id"]
        credits = int(metadata["credits"])

        billing_service.add_credits(user_id, credits)

    return {"status": "ok"}
