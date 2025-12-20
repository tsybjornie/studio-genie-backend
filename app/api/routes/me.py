from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.core.security import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """
    Get everything for dashboard in one call:
    - User info (email, credits, plan)
    - All user's videos
    
    This is more efficient than frontend making 2 separate API calls.
    """
    user_id = current_user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Get user info
        cur.execute(
            """
            SELECT id, email, credits, plan, subscription_status
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        user_row = cur.fetchone()
        
        if not user_row:
            cur.close()
            conn.close()
            return {"error": "User not found"}, 404
        
        # Get all videos for this user
        cur.execute(
            """
            SELECT id, prompt, status, video_url, created_at, image_url, style
            FROM videos
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        video_rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Build response
        user_data = {
            "id": user_row["id"],
            "email": user_row["email"],
            "credits": user_row.get("credits", 0),
            "plan": user_row.get("plan", "free"),
            "subscription_status": user_row.get("subscription_status")
        }
        
        videos = []
        for row in video_rows:
            videos.append({
                "id": row["id"],
                "prompt": row.get("prompt"),
                "status": row.get("status", "queued"),
                "output_url": row.get("video_url"),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "image_url": row.get("image_url"),
                "style": row.get("style")
            })
        
        return {
            "user": user_data,
            "videos": videos,
            "stats": {
                "total_videos": len(videos),
                "credits_remaining": user_data["credits"]
            }
        }
        
    except Exception as e:
        cur.close()
        conn.close()
        raise
