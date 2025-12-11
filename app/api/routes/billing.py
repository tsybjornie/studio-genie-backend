from fastapi import APIRouter, HTTPException
from app.services.billing_service import billing_service
from pydantic import BaseModel

router = APIRouter()

class CheckoutSessionRequest(BaseModel):
    price_id: str

@router.options("/create-checkout-session")
async def options_checkout():
    return {"status": "ok"}

@router.post("/create-checkout-session")
async def create_session(payload: CheckoutSessionRequest):
    try:
        url = await billing_service.create_session(payload.price_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
