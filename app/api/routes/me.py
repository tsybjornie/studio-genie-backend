from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_connection
from app.core.security import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """
    Get everything for dashboard in one call:
    - User info (email, credits)
    - All user's videos (if table exists)
    
    Returns defensive defaults for missing data.
    """
    user_id = current_user.get("user_id")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Get user info (only query columns that exist)
        cur.execute(
            """
            SELECT id, email, credits
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        user_row = cur.fetchone()
        
        if not user_row:
            cur.close()
            conn.close()
            logger.error(f"[DASHBOARD] User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build user data with defensive defaults
        user_data = {
            "id": user_row["id"],
            "email": user_row["email"] or "unknown@example.com",
            "credits": user_row.get("credits") or 0,
            "plan": "starter",  # Default plan
            "subscription_status": None
        }
        
        # Try to get videos (table might not exist or be empty)
        videos = []
        try:
            cur.execute(
                """
                SELECT id, prompt, status, video_url, created_at
                FROM videos
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 100
                """,
                (user_id,)
            )
            video_rows = cur.fetchall()
            
            # Safely build video list with null handling
            for row in (video_rows or []):
                try:
                    videos.append({
                        "id": row.get("id"),
                        "prompt": row.get("prompt") or "",
                        "status": row.get("status") or "unknown",
                        "output_url": row.get("video_url"),
                        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                    })
                except Exception as video_err:
                    logger.warning(f"[DASHBOARD] Failed to parse video row: {video_err}")
                    continue
                    
        except Exception as video_query_err:
            logger.warning(f"[DASHBOARD] Video query failed (table might not exist): {video_query_err}")
            videos = []  # Safe default
        
        cur.close()
        conn.close()
        
        logger.info(f"[DASHBOARD] Returned {len(videos)} videos for user {user_data['email']}")
        
        return {
            "user": user_data,
            "videos": videos,  # Always returns list, never None
            "stats": {
                "total_videos": len(videos),
                "credits_remaining": user_data["credits"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DASHBOARD] Unexpected error: {e}", exc_info=True)
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")
