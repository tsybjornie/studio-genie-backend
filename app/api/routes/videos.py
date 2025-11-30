from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from typing import List
import logging

from app.schemas.video_schemas import (
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoListResponse,
    VideoDetailResponse
)
from app.core.security import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.services.credit_service import credit_service
from app.services.video_service import video_service
from app.services.billing_service import billing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Videos"])


# -----------------------------------------------------------
# ACCESS CHECK — ENFORCE SUBSCRIPTIONS & CREDITS
# -----------------------------------------------------------
async def assert_user_has_access(user):
    """
    Prevent free users from generating unlimited videos.
    """

    # ⭐ If user has an active subscription → allow (credits may still apply)
    if user.get("subscription_status") == "active":
        return

    # ⭐ If user has credits → allow
    credits = user.get("credits_remaining", 0)
    if credits > 0:
        return

    # ⭐ Free user with 0 credits → block
    raise HTTPException(
        status_code=402,  # Payment Required
        detail="Not enough credits. Please upgrade or purchase credits."
    )


# -----------------------------------------------------------
# GENERATE VIDEO
# -----------------------------------------------------------
@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: VideoGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    v2 Logic:
    - Check subscription OR credits
    - If subscription active → discount
    - Deduct credits
    - Create video DB entry
    - Start MGX generation process
    """

    try:
        user_id = current_user["id"]

        # ---------------------------------------------------
        # 1. ACCESS CONTROL (subscription or credits)
        # ---------------------------------------------------
        await assert_user_has_access(current_user)

        # ---------------------------------------------------
        # 2. COST CALCULATION
        # ---------------------------------------------------
        BASE_COST = settings.CREDITS_PER_VIDEO  # usually 5 credits

        # Discount for subscription users
        if current_user.get("subscription_status") == "active":
            COST = max(1, BASE_COST // 2)  # 50% discount
        else:
            COST = BASE_COST

        # ---------------------------------------------------
        # 3. DEDUCT CREDITS
        # ---------------------------------------------------
        new_balance = credit_service.deduct_credits(
            db=db,
            user_id=user_id,
            amount=COST
        )

        logger.info(f"[CREDITS] Deducted {COST} from {user_id}. Remaining={new_balance}")

        # ---------------------------------------------------
        # 4. CREATE VIDEO RECORD
        # ---------------------------------------------------
        video = video_service.create_video_record(
            user_id=user_id,
            prompt=request.prompt,
            style=request.style,
            image_url=request.image_url
        )

        video_id = video["id"]

        # ---------------------------------------------------
        # 5. START MGX GENERATION (background orchestration)
        # ---------------------------------------------------
        from app.workers.video_generation import start_generation_task

        start_generation_task.delay(
            video_id=video_id,
            user_id=user_id,
            prompt=request.prompt,
            style=request.style,
            image_url=request.image_url
        )

        return VideoGenerateResponse(
            job_id=video_id,
            video_id=video_id,
            status="queued",
            message="Video generation started.",
            credits_used=COST,
            credits_remaining=new_balance
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Video generation error: {str(e)}")
        raise HTTPException(500, "Failed to generate video")


# -----------------------------------------------------------
# LIST VIDEOS
# -----------------------------------------------------------
@router.get("", response_model=List[VideoListResponse])
async def list_videos(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    try:
        videos = video_service.get_user_videos(current_user["id"], limit, offset)

        return [
            VideoListResponse(
                id=v["id"],
                prompt=v["prompt"],
                style=v["style"],
                status=v["status"],
                video_url=v.get("video_url"),
                created_at=v["created_at"],
            )
            for v in videos
        ]

    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        raise HTTPException(500, "Failed to list videos")


# -----------------------------------------------------------
# VIDEO DETAILS
# -----------------------------------------------------------
@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        video = video_service.get_video(video_id, current_user["id"])

        return VideoDetailResponse(
            id=video["id"],
            user_id=video["user_id"],
            prompt=video["prompt"],
            style=video["style"],
            image_url=video.get("image_url"),
            status=video["status"],
            video_url=video.get("video_url"),
            created_at=video["created_at"]
        )

    except Exception as e:
        logger.error(f"Error fetching video: {str(e)}")
        raise HTTPException(500, "Failed to fetch video")


# -----------------------------------------------------------
# DOWNLOAD FINISHED VIDEO
# -----------------------------------------------------------
@router.get("/{video_id}/download")
async def download_video(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        video = video_service.get_video(video_id, current_user["id"])

        if video["status"] != "done":
            raise HTTPException(400, "Video is not ready yet.")

        if not video.get("video_url"):
            raise HTTPException(404, "Video file not found.")

        return RedirectResponse(url=video["video_url"])

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(500, "Failed to download video")
