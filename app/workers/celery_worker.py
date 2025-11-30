from celery import Celery
from app.core.config import settings
from app.services.video_service import video_service
from app.utils.storage import storage_service
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "studio_genie_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


def generate_placeholder_video(prompt: str, style: str, image_url: str = None) -> str:
    """
    Generate a placeholder video using FFmpeg
    
    This is a stub function that creates a simple video.
    In production, this would call the MGX API.
    
    Args:
        prompt: Video generation prompt
        style: Video style
        image_url: Optional image URL
        
    Returns:
        Path to generated video file
    """
    try:
        # Create temporary output file
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        output_path = output_file.name
        output_file.close()
        
        # Generate a simple 5-second video with FFmpeg
        # This creates a colored background with text overlay
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'color=c=blue:s=1920x1080:d=5',
            '-vf', f"drawtext=text='Studio Génie\\nPrompt: {prompt[:50]}\\nStyle: {style}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
            '-c:v', 'libx264',
            '-t', '5',
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]
        
        # Run FFmpeg
        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception("Video generation failed")
        
        logger.info(f"Generated placeholder video: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating placeholder video: {str(e)}")
        raise


@celery_app.task(name="generate_video_task", bind=True)
def generate_video_task(self, video_id: str, user_id: str, prompt: str, style: str, image_url: str = None):
    """
    Celery task for video generation
    
    Args:
        video_id: Video record ID
        user_id: User ID
        prompt: Video generation prompt
        style: Video style
        image_url: Optional image URL
    """
    try:
        logger.info(f"Starting video generation for video_id: {video_id}")
        
        # Update status to processing
        video_service.update_video_status(video_id, 'processing')
        
        # Generate video (placeholder implementation)
        # In production, this would call the MGX API
        video_path = generate_placeholder_video(prompt, style, image_url)
        
        # Upload to Supabase storage
        video_url = storage_service.upload_video(video_path, user_id, video_id)
        
        # Update status to done with video URL
        video_service.update_video_status(video_id, 'done', video_url)
        
        # Clean up temporary file
        if os.path.exists(video_path):
            os.remove(video_path)
        
        logger.info(f"Video generation completed for video_id: {video_id}")
        
        return {
            'status': 'success',
            'video_id': video_id,
            'video_url': video_url
        }
    
    except Exception as e:
        logger.error(f"Video generation failed for video_id {video_id}: {str(e)}")
        
        # Update status to failed
        try:
            video_service.update_video_status(video_id, 'failed')
        except:
            pass
        
        raise
