from fastapi import APIRouter, HTTPException, Depends
from app.schemas.credit_schemas import CreditsResponse
from app.core.security import get_current_user
from app.services.credit_service import credit_service
import logging

logger = logging.getLogger(__name__)

# THIS MUST EXIST — Render import error comes from this
router = APIRouter(prefix="/credits", tags=["Credits"])


@router.get("", response_model=CreditsResponse)
async def get_credits(current_user: dict = Depends(get_current_user)):
    """
    Returns:
        - credits_remaining
        - has_trial_used
        - plan
    """
    try:
        data = credit_service.get_user_credits(current_user["id"])

        return CreditsResponse(
            credits_remaining=data["credits_remaining"],
            has_trial_used=data["has_trial_used"],
            plan=data["plan"]
        )

    except Exception as e:
        logger.error(f"[CREDITS] Error fetching credits: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch credits")


# OPTIONAL — CLAIM TRIAL
@router.post("/trial", response_model=CreditsResponse)
async def claim_trial(current_user: dict = Depends(get_current_user)):
    """
    Gives 3 credits (1 video) if user hasn't used trial.
    """
    try:
        success = credit_service.apply_trial(current_user["id"])

        if not success:
            raise HTTPException(status_code=400, detail="Trial already used")

        data = credit_service.get_user_credits(current_user["id"])

        return CreditsResponse(
            credits_remaining=data["credits_remaining"],
            has_trial_used=data["has_trial_used"],
            plan=data["plan"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TRIAL] Error applying trial: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply trial")
