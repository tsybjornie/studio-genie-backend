from pydantic import BaseModel


class CreditsResponse(BaseModel):
    """Schema for credits balance response"""
    credits_remaining: int
    has_trial_used: bool
    plan: str | None = None


class AddCreditsRequest(BaseModel):
    """Schema for adding credits"""
    amount: int  # Number of credits to add


class AddCreditsResponse(BaseModel):
    """Schema for add credits response"""
    success: bool
    credits_added: int
    credits_remaining: int
    message: str
