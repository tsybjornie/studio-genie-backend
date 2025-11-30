from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCredits(BaseModel):
    id: str
    user_id: str
    credits: int
    updated_at: datetime

class CreditTransaction(BaseModel):
    id: str
    user_id: str
    amount: int
    type: str  # 'subscription', 'topup', 'usage'
    reference_id: Optional[str] = None  # coinbase charge id or subscription id
    created_at: datetime
