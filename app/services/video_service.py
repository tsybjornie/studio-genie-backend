from app.core.database import get_db
from app.core.config import settings
from fastapi import HTTPException
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VideoService:
    """Service for managing video generation and retrieval"""
    
    def __init__(self):
        self.db = get_db()
    
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
            
            video_data = {
                'id': video_id,
                'user_id': user_id,
                'prompt': prompt,
                'style': style,
                'image_url': image_url,
                'status': 'queued',
                'video_url': None,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.db.service_client.table('videos').insert(video_data).execute()
            
            logger.info(f"Created video record {video_id} for user {user_id}")
            
            return response.data[0]
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
            update_data = {'status': status}
            
            if video_url:
                update_data['video_url'] = video_url
            
            response = self.db.service_client.table('videos').update(
                update_data
            ).eq('id', video_id).execute()
            
            logger.info(f"Updated video {video_id} status to {status}")
            
            return response.data[0] if response.data else None
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
            query = self.db.service_client.table('videos').select('*').eq('id', video_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            response = query.execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="Video not found")
            
            return response.data[0]
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
            response = self.db.service_client.table('videos').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            return response.data
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
            video = self.get_video(video_id, user_id)
            
            # Delete from database
            response = self.db.service_client.table('videos').delete().eq('id', video_id).execute()
            
            logger.info(f"Deleted video {video_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete video")


# Global video service instance
video_service = VideoService()
