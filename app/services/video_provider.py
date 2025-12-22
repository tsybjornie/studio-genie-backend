import asyncio
import uuid
import random


class MockVideoProvider:
    """
    Mock video provider for testing and demos.
    Returns realistic-looking video and thumbnail URLs.
    """
    
    async def generate(self, prompt: str, duration: int) -> dict:
        """
        Simulate video generation with a delay.
        Returns both video URL and thumbnail URL.
        """
        # Simulate processing time (3 seconds)
        await asyncio.sleep(3)
        
        video_id = str(uuid.uuid4())
        
        # Use random stock video thumbnails for variety
        thumbnail_styles = [
            "https://images.unsplash.com/photo-1611162617474-5b21e879e113",  # Professional video
            "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d",  # Creative content
            "https://images.unsplash.com/photo-1492619375914-88005aa9e8fb",  # Modern tech
            "https://images.unsplash.com/photo-1536240478700-b869070f9279",  # Business content
        ]
        
        # Pick a random thumbnail
        thumbnail = random.choice(thumbnail_styles) + "?w=400&h=225&fit=crop"
        
        return {
            "video_url": f"https://example.com/mock-videos/{video_id}.mp4",
            "thumbnail_url": thumbnail,
            "duration": duration,
            "status": "completed"
        }


mock_provider = MockVideoProvider()
