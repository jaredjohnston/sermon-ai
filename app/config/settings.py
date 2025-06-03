import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and constants"""
    
    # API Keys
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 4 * 1024 * 1024 * 1024  # 4GB
    CHUNK_SIZE: int = 1024 * 1024  # 1MB chunks for streaming
    UPLOAD_TIMEOUT: int = 600  # 10 minutes
    
    # Media Types
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a",
        "audio/mpeg3", "audio/x-mpeg-3", "audio/m4a",
    ]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/mpeg", "video/webm"]
    ALLOWED_MEDIA_TYPES: List[str] = ALLOWED_AUDIO_TYPES + ALLOWED_VIDEO_TYPES
    
    # Deepgram Settings
    SEGMENT_CLASSIFIER_PROMPT: str = """You are an expert at analyzing church service transcripts. Your task is to classify the following segment of a church service transcript into one of these categories:
- WORSHIP: Musical worship, songs, prayers during worship
- WELCOME: Welcoming new visitors, announcements at the start
- SERMON: The main sermon message, including opening/closing prayers
- ADMIN: Church announcements, upcoming events
- TITHING: Offering, giving, financial matters
- OTHER: Any other segments

Respond in the following JSON format only:
{
    "type": "WORSHIP|WELCOME|SERMON|ADMIN|TITHING|OTHER",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification"
}"""

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Sermon AI"
    VERSION: str = "1.0.0"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://your-frontend-domain.com",
    ]

settings = Settings() 