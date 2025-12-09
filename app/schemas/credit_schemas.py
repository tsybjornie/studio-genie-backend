from pydantic import BaseModel


class CreditsResponse(BaseModel):
    """
    Response model returned to frontend:
    - Dashboard credit display
    - Header balance display
    - Checkout validation
    """
    credits_remaining: int
    has_trial_used: bool
    plan: str | None = None

    class Config:
        from_attributes = True
