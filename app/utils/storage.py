import logging

logger = logging.getLogger(__name__)

class StorageService:
    """
    Mock Storage Service for Custom Database Layer.
    """
    def upload_video(self, file_path: str, user_id: str = "mock_user", video_id: str = "mock_video") -> str:
        """
        Mock upload video.
        Returns a fake URL.
        """
        logger.info(f"[STORAGE MOCK] Uploading {video_id} for user {user_id} from {file_path}")
        return f"https://mock-storage.com/{video_id}.mp4"

storage = StorageService()
