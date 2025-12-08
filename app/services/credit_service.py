from app.core.database import db
from app.core.config import settings

# Mapping Price IDs to Credit Amounts
CREDIT_PACKS = {
    settings.STRIPE_PRICE_STARTER: 60,
    settings.STRIPE_PRICE_CREATOR: 150,
    settings.STRIPE_PRICE_PRO: 360,
}


async def apply_credits(email: str, price_id: str):
    """
    Applies credits to a user account based on the purchased price_id.
    Adapts user request logic to work with Supabase (PostgreSQL) backend.
    """
    credits_to_add = CREDIT_PACKS.get(price_id)
    if not credits_to_add:
        print(f"[CreditService] Unknown price_id: {price_id}")
        return

    try:
        # 1. Find user by email (Supabase)
        response = db.service_client.table("users").select("id, credits_remaining").eq("email", email).single().execute()
        user = response.data
        
        if not user:
            print(f"[CreditService] User not found for email: {email}")
            return

        current_balance = user.get("credits_remaining") or 0
        new_balance = current_balance + credits_to_add

        # 2. Update credits
        db.service_client.table("users").update(
            {"credits_remaining": new_balance}
        ).eq("email", email).execute()

        print(f"[CreditService] Added {credits_to_add} credits to {email}. New Balance: {new_balance}")
        return new_balance

    except Exception as e:
        print(f"[CreditService] Error applying credits: {e}")
        return None
