from app.core.database import get_db
from app.core.config import settings
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Service for handling file storage in Supabase"""
    
    def __init__(self):
        self.db = get_db()
        self.bucket_name = settings.SUPABASE_STORAGE_BUCKET
    
    def upload_video(self, file_path: str, user_id: str, video_id: str) -> str:
        """
        Upload a video file to Supabase storage
        
        Args:
            file_path: Local path to the video file
            user_id: ID of the user who owns the video
            video_id: ID of the video record
            
        Returns:
            Public URL of the uploaded video
        """
        try:
            # Generate unique filename
            filename = f"{user_id}/{video_id}.mp4"
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase storage
            response = self.db.service_client.storage.from_(self.bucket_name).upload(
                filename,
                file_data,
                file_options={"content-type": "video/mp4"}
            )
            
            # Get public URL
            public_url = self.db.service_client.storage.from_(self.bucket_name).get_public_url(filename)
            
            logger.info(f"Video uploaded successfully: {filename}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload video: {str(e)}")
            raise
    
    def delete_video(self, user_id: str, video_id: str) -> bool:
        """
        Delete a video file from Supabase storage
        
        Args:
            user_id: ID of the user who owns the video
            video_id: ID of the video record
            
        Returns:
            True if deletion was successful
        """
        try:
            filename = f"{user_id}/{video_id}.mp4"
            
            self.db.service_client.storage.from_(self.bucket_name).remove([filename])
            
            logger.info(f"Video deleted successfully: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete video: {str(e)}")
            return False
    
    def get_video_url(self, user_id: str, video_id: str) -> str:
        """
        Get the public URL for a video
        
        Args:
            user_id: ID of the user who owns the video
            video_id: ID of the video record
            
        Returns:
            Public URL of the video
        """
        filename = f"{user_id}/{video_id}.mp4"
        return self.db.service_client.storage.from_(self.bucket_name).get_public_url(filename)


# Global storage service instance
storage_service = StorageService()
