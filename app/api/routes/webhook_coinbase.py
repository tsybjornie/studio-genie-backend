from fastapi import APIRouter, Request
from app.services.coinbase_service import coinbase_service

router = APIRouter(prefix="/webhooks/coinbase")

@router.post("")
async def coinbase_webhook(payload: dict):
    event = payload["event"]

    if not coinbase_service.verify_event(event):
        return {"status": "ignored"}

    user_id = event["data"]["metadata"]["user_id"]
    pack_key = event["data"]["metadata"]["pack_key"]

    coinbase_service.process_payment(user_id, pack_key)

    return {"status": "processed"}
