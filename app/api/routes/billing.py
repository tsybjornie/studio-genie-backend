from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.billing_service import billing_service

router = APIRouter()

class CheckoutSessionRequest(BaseModel):
    price_id: str

@router.options("/create-checkout-session")
async def options_session():
    return {"status": "ok"}

@router.post("/create-checkout-session")
async def create_checkout(payload: CheckoutSessionRequest):
    try:
        url = await billing_service.create_session(payload.price_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
