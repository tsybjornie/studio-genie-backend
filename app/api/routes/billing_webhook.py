from fastapi import APIRouter, Request, HTTPException
import stripe
from app.core.config import settings
from app.services.credit_service import apply_credits

router = APIRouter(prefix="/billing/stripe")

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    # Subscription created or renewed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email")
        
        # Note: Line items might not be in the webhook event unless expanded.
        # Ideally we should fetch the session from Stripe to be sure, but using user's simple logic for now.
        # Fallback handling could be added if needed.
        lines = session.get("line_items", {}).get("data", [])
        if not lines:
             # Try to retrieve session if line_items are missing
             session = stripe.checkout.Session.retrieve(
                 session["id"], expand=["line_items"]
             )
             lines = session.get("line_items", {}).get("data", [])
        
        if lines and customer_email:
            price_id = lines[0]["price"]["id"]
            await apply_credits(customer_email, price_id)

    return {"status": "ok"}
