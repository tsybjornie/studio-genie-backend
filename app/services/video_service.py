from app.core.database import get_connection
from app.core.config import settings
from fastapi import HTTPException
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VideoService:
    """Service for managing video generation and retrieval"""
    
    def create_video_record(self, user_id: str, prompt: str, style: str, image_url: str = None) -> dict:
        """
        Create a new video record in the database
        
        Args:
            user_id: User ID
            prompt: Video generation prompt
            style: Video style
            image_url: Optional image URL
            
        Returns:
            Created video record
        """
        try:
            video_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                INSERT INTO videos (id, user_id, prompt, style, image_url, status, video_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, prompt, style, image_url, status, video_url, created_at
                """,
                (video_id, user_id, prompt, style, image_url, 'queued', None, created_at)
            )
            
            video_record = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Created video record {video_id} for user {user_id}")
            
            return dict(video_record)
        except Exception as e:
            logger.error(f"Error creating video record: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create video record")
    
    def update_video_status(self, video_id: str, status: str, video_url: str = None) -> dict:
        """
        Update video status and optionally set video URL
        
        Args:
            video_id: Video ID
            status: New status (queued, processing, done, failed)
            video_url: Optional video URL when status is 'done'
            
        Returns:
            Updated video record
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            if video_url:
                cur.execute(
                    """
                    UPDATE videos 
                    SET status = %s, video_url = %s
                    WHERE id = %s
                    RETURNING id, user_id, prompt, style, image_url, status, video_url, created_at
                    """,
                    (status, video_url, video_id)
                )
            else:
                cur.execute(
                    """
                    UPDATE videos 
                    SET status = %s
                    WHERE id = %s
                    RETURNING id, user_id, prompt, style, image_url, status, video_url, created_at
                    """,
                    (status, video_id)
                )
            
            video_record = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Updated video {video_id} status to {status}")
            
            return dict(video_record) if video_record else None
        except Exception as e:
            logger.error(f"Error updating video status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update video status")
    
    def get_video(self, video_id: str, user_id: str = None) -> dict:
        """
        Get a video by ID
        
        Args:
            video_id: Video ID
            user_id: Optional user ID to verify ownership
            
        Returns:
            Video record
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            if user_id:
                cur.execute(
                    "SELECT * FROM videos WHERE id = %s AND user_id = %s",
                    (video_id, user_id)
                )
            else:
                cur.execute(
                    "SELECT * FROM videos WHERE id = %s",
                    (video_id,)
                )
            
            video_record = cur.fetchone()
            cur.close()
            conn.close()
            
            if not video_record:
                raise HTTPException(status_code=404, detail="Video not found")
            
            return dict(video_record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching video: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch video")
    
    def get_user_videos(self, user_id: str, limit: int = 50, offset: int = 0) -> list:
        """
        Get all videos for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of videos to return
            offset: Offset for pagination
            
        Returns:
            List of video records
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                SELECT * FROM videos 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset)
            )
            
            videos = cur.fetchall()
            cur.close()
            conn.close()
            
            return [dict(video) for video in videos]
        except Exception as e:
            logger.error(f"Error fetching user videos: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch videos")
    
    def delete_video(self, video_id: str, user_id: str) -> bool:
        """
        Delete a video record
        
        Args:
            video_id: Video ID
            user_id: User ID to verify ownership
            
        Returns:
            True if successful
        """
        try:
            # Verify ownership
            self.get_video(video_id, user_id)
            
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute(
                "DELETE FROM videos WHERE id = %s",
                (video_id,)
            )
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Deleted video {video_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete video")


# Global video service instance
video_service = VideoService()
