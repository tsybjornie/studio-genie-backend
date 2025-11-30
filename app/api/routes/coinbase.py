from fastapi import APIRouter, Request, HTTPException, Depends
from app.core.config import settings
from app.core.database import get_db, SupabaseClient
from app.services.credit_service import credit_service
from app.utils.logger import logger
import hashlib
import hmac
import json

router = APIRouter(prefix="/coinbase", tags=["Coinbase"])

# 🔐 Coinbase checkout → credits mapping
CHECKOUT_MAP = {
    "285ac9ac-e2b6-4a6e-9d60-1b20d43af8aa": ("starter", 60),      # plan
    "51f73869-536d-4125-abcd-15473fb4e8aa": ("creator", 150),    # plan
    "b8f7f2d3-10b1-4538-8b11-b7888e452e04": ("pro", 360),         # plan
    "e1caeb58-0bd1-47ad-839b-a75810bc83d3": ("topup", 30),       # credits
    "adfe2706-9b61-4611-a173-c34904b0fe77": ("topup", 100),
    "191ee0bf-f379-4f64-b5dd-0c5c6a990863": ("topup", 300),
    "2a771791-5a9f-47ad-bcbe-bc57cc2af63e": ("topup", 1000),
}

def verify_signature(request: Request, body: bytes):
    """Verify Coinbase webhook signature."""
    signature = request.headers.get("X-CC-Webhook-Signature")
    secret = settings.COINBASE_WEBHOOK_SECRET.encode()
    computed = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)

@router.post("/webhook")
async def coinbase_webhook(request: Request, db: SupabaseClient = Depends(get_db)):
    body = await request.body()

    if not verify_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid Coinbase signature")

    payload = json.loads(body)
    event_type = payload["event"]["type"]

    if event_type != "charge:confirmed":
        return {"status": "ignored"}

    charge = payload["event"]["data"]
    checkout_id = charge["checkout"]["id"]
    reference_id = charge["id"]
    user_id = charge["metadata"]["user_id"]

    if checkout_id not in CHECKOUT_MAP:
        logger.error(f"Unknown checkout ID: {checkout_id}")
        return {"status": "error"}

    purchase_type, value = CHECKOUT_MAP[checkout_id]

    # Prevent duplicate crediting
    existing = db.service_client.table("payments").select("*").eq("reference_id", reference_id).execute()
    if existing.data:
        return {"status": "duplicate"}

    # Add credits for both topup and subscription purchases
    credit_service.add_credits(user_id, value, reason="coinbase")

    return {"status": "success"}
