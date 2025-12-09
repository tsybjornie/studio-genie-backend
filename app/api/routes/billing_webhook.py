from fastapi import APIRouter, Request, HTTPException
import stripe

from app.core.config import settings
from app.services.credit_service import credit_service
from app.models.user import User

router = APIRouter(prefix="/webhook")

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe")
async def stripe_webhook(request: Request):
    raw_body = await request.body()
    sig = request.headers.get("stripe-signature")

    if sig is None:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            raw_body,
            sig,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    event_type = event["type"]

    # ==============================================
    # INVOICE PAID → APPLY SUBSCRIPTION CREDITS
    # ==============================================
    if event_type == "invoice.paid":
        invoice = event["data"]["object"]

        lines = invoice.get("lines", {}).get("data", [])
        if not lines:
            return {"status": "ignored", "reason": "no_line_items"}

        line = lines[0]
        price_id = line["price"]["id"]

        email = invoice.get("customer_email")
        if not email:
            return {"status": "ignored", "reason": "missing_email"}

        user = User.get_by_email(email)
        if not user:
            return {"status": "ignored", "reason": "user_not_found"}

        credit_service.apply_subscription_credits(user.id, price_id)

        return {"status": "ok", "handled": "invoice.paid"}

    # Ignore everything else
    return {"status": "ignored", "event": event_type}
