from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("")
async def get_videos(current_user: dict = Depends(get_current_user)):
    """
    Get all videos for current user.
    Returns list of videos with status, created_at, etc.
    """
    user_id = current_user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            SELECT id, prompt, status, video_url, created_at, image_url, style
            FROM videos
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        videos = []
        for row in rows:
            videos.append({
                "id": row["id"],
                "prompt": row.get("prompt"),
                "status": row.get("status", "queued"),
                "output_url": row.get("video_url"),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "image_url": row.get("image_url"),
                "style": row.get("style")
            })
        
        return videos
        
    except Exception as e:
        cur.close()
        conn.close()
        raise


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
