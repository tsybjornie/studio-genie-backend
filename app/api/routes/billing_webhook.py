from fastapi import APIRouter, Request, HTTPException
import stripe
from app.core.config import settings
from app.services.credit_service import apply_credits
from app.models.user import User  # adjust to your project structure

router = APIRouter(prefix="/webhook")

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Only handle invoice.paid for subscriptions
    if event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        # Safety check: ensure lines exist
        lines = invoice.get("lines", {}).get("data", [])
        if lines:
            price_id = lines[0]["price"]["id"]
            # invoice object has customer_email
            customer_email = invoice.get("customer_email")

            if customer_email:
                user = User.get_by_email(customer_email)
                if user:
                    apply_credits(user, price_id)

    return {"status": "ok"}
