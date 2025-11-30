from fastapi import APIRouter, Request, HTTPException
import stripe
from app.core.config import settings
from app.services.stripe_service import stripe_service

router = APIRouter(prefix="/webhooks/stripe")

@router.post("")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "invoice.payment_succeeded":
        data = event["data"]["object"]
        stripe_sub_id = data["subscription"]
        user_id = data["client_reference_id"]
        plan = data["lines"]["data"][0]["price"]["nickname"]

        stripe_service.process_invoice_paid(stripe_sub_id, user_id, plan)

    return {"status": "ok"}
