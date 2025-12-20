from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("")
async def get_videos():
    """
    Get all videos for current user.
    Stub endpoint - returns empty list.
    """
    return []


@router.post("")
async def create_video(
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new video generation request.
    Deducts 3 credits and creates video record.
    """
    user_id = current_user.get("user_id")
    script = payload.get("script", "")
    language = payload.get("language", "en")
    
    if not script:
        return {"error": "Script is required"}, 400
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Check credits
        cur.execute(
            "SELECT credits FROM users WHERE id = %s",
            (user_id,)
        )
        user = cur.fetchone()
        
        if not user or user.get("credits", 0) < 3:
            cur.close()
            conn.close()
            return {"error": "Not enough credits"}, 400
        
        # Deduct credits
        cur.execute(
            "UPDATE users SET credits = credits - 3 WHERE id = %s",
            (user_id,)
        )
        
        # Create video record
        cur.execute(
            """
            INSERT INTO videos (user_id, prompt, status, style)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, script, "queued", language)
        )
        
        video_id = cur.fetchone()["id"]
        conn.commit()
        
        cur.close()
        conn.close()
        
        return {"id": video_id, "status": "queued"}
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise
