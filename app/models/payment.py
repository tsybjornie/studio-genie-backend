from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class Payment(BaseModel):
    """Payment model"""
    id: str
    user_id: str
    provider: str  # stripe or coinbase
    credits_added: int
    amount_usd: Decimal
    status: str  # pending, completed, failed
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """Schema for creating a payment record"""
    user_id: str
    provider: str
    credits_added: int
    amount_usd: Decimal
    status: str = "pending"
