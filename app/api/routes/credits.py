from fastapi import APIRouter, HTTPException, Depends
from app.schemas.credit_schemas import CreditsResponse
from app.core.security import get_current_user
from app.services.credit_service import credit_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["Credits"])


@router.get("", response_model=CreditsResponse)
async def get_credits(current_user: dict = Depends(get_current_user)):
    """
    Get user's credit balance
    
    Returns the current credit balance, trial status, and subscription plan.
    """
    try:
        user_data = credit_service.get_user_credits(current_user['id'])
        
        return CreditsResponse(
            credits_remaining=user_data['credits_remaining'],
            has_trial_used=user_data['has_trial_used'],
            plan=user_data.get('plan')
        )
    
    except Exception as e:
        logger.error(f"Error fetching credits: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch credits")
