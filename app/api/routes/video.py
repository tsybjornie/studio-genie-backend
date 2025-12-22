from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import uuid

from app.models.video_job import VideoJob
from app.services.video_provider import mock_provider
from app.services.video_credit_policy import credits_required
from app.core.security import get_current_user

router = APIRouter()


@router.post("/video/generate")
async def generate_video(
    prompt: str,
    duration_seconds: int,
    current_user=Depends(get_current_user),
):
    """
    Generate video using mock provider.
    Deducts credits immediately and returns video URL.
    """
    # 1️⃣ Calculate credits needed
    required = credits_required(duration_seconds)
    
    user_id = current_user.get("user_id")
    
    # Get user's current credits from database
    from app.core.database import get_connection
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT credits FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    
    if not result:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    current_credits = result["credits"] or 0

    if current_credits < required:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough credits")

    # 2️⃣ Create job
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    job = VideoJob(
        id=job_id,
        user_id=user_id,
        prompt=prompt,
        duration_seconds=duration_seconds,
        status="processing",
        provider="mock",
        created_at=now,
        updated_at=now,
    )

    # 3️⃣ Deduct credits immediately (IMPORTANT)
    new_credits = current_credits - required
    cur.execute(
        "UPDATE users SET credits = %s WHERE id = %s",
        (new_credits, user_id)
    )
    conn.commit()

    # 4️⃣ Generate video
    try:
        result = await mock_provider.generate(prompt, duration_seconds)
        job.status = "completed"
        job.video_url = result["video_url"]
        thumbnail_url = result.get("thumbnail_url")
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        thumbnail_url = None

    job.updated_at = datetime.utcnow()
    
    cur.close()
    conn.close()

    return {
        "job_id": job.id,
        "status": job.status,
        "video_url": job.video_url,
        "thumbnail_url": thumbnail_url,
        "duration": duration_seconds,
        "credits_used": required,
        "credits_left": new_credits,
    }
