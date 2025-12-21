import asyncio
import uuid


class MockVideoProvider:
    async def generate(self, prompt: str, duration: int) -> str:
        # Simulate processing time
        await asyncio.sleep(3)

        # Return a fake but real-looking video URL
        return f"https://example.com/mock-videos/{uuid.uuid4()}.mp4"


mock_provider = MockVideoProvider()
