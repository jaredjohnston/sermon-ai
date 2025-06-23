import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024 * 1024  # 50GB (Supabase Pro+ limit)
    CHUNK_SIZE: int = 1024 * 1024  # 1MB chunks for streaming
    UPLOAD_TIMEOUT: int = 1800  # 30 minutes for large files
    
    # TUS Upload Settings
    TUS_CHUNK_SIZE: int = 6 * 1024 * 1024  # 6MB chunks (Supabase recommended)
    TUS_THRESHOLD: int = 6 * 1024 * 1024  # Use TUS for files > 6MB
    
    # Callback Settings
    CALLBACK_URL: str = os.getenv("CALLBACK_URL", "http://localhost:8000/api/v1/transcription/callback")
    
    # Media Types
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a",
        "audio/mpeg3", "audio/x-mpeg-3", "audio/m4a",
    ]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/mpeg", "video/webm"]
    ALLOWED_MEDIA_TYPES: List[str] = ALLOWED_AUDIO_TYPES + ALLOWED_VIDEO_TYPES
    
    # OpenAI Settings
    DEFAULT_MODEL: str = "gpt-4-turbo-preview"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    
    # Prompts
    SEGMENT_CLASSIFIER_PROMPT: str = """
    Analyze this segment of a church service transcript and classify it into one of these categories:
    - sermon: The main message/teaching
    - prayer: Prayer segments
    - worship: Music and worship
    - admin: Announcements, logistics
    - other: Anything else

    Text to classify:
    {text}

    Respond in JSON format with:
    {
        "type": "category_name",
        "confidence": 0.0-1.0 score
    }
    """

    DEVOTIONAL_PROMPT: str = """
    Create a thoughtful daily devotional based on this sermon segment. Include:
    1. A key verse or biblical reference
    2. Main insight from the sermon
    3. Personal application
    4. A reflection question
    5. A short prayer

    Sermon text:
    {text}

    Respond in JSON format with:
    {
        "content": "devotional text with clear sections",
        "metadata": {
            "key_verse": "reference",
            "theme": "main theme"
        }
    }
    """

    SUMMARY_PROMPT: str = """
    Create a concise summary of this sermon that captures:
    1. Main theme/topic
    2. Key points (2-3)
    3. Scripture references
    4. Practical takeaways

    Sermon text:
    {text}

    Respond in JSON format with:
    {
        "content": "formatted summary with sections",
        "metadata": {
            "theme": "main theme",
            "scriptures": ["list", "of", "references"]
        }
    }
    """

    DISCUSSION_PROMPT: str = """
    Create engaging small group discussion questions based on this sermon:
    - Mix of comprehension and application questions
    - Include relevant scripture references
    - Add follow-up questions for deeper discussion
    - Include 1-2 real-life scenarios to discuss

    Sermon text:
    {text}

    Respond in JSON format with:
    {
        "content": "formatted questions with clear sections",
        "metadata": {
            "theme": "discussion theme",
            "scripture_focus": ["main", "verses"]
        }
    }
    """

    WHATS_ON_PROMPT: str = """
    Create a clear, engaging announcement summary from this administrative segment:
    - Upcoming events with dates/times
    - Important announcements
    - Any action items for the congregation
    - Contact information if provided

    Admin text:
    {text}

    Respond in JSON format with:
    {
        "content": "formatted announcements",
        "metadata": {
            "events": [{"title": "event", "date": "date"}],
            "priority_items": ["list", "of", "priorities"]
        }
    }
    """

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Sermon AI"
    VERSION: str = "1.0.0"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://your-frontend-domain.com",
    ]

    # Content Generation Settings
    CONTENT_PROMPTS: Dict[str, Dict[str, Any]] = {
        "sermon": {
            "devotional": {
                "prompt": DEVOTIONAL_PROMPT,
                "temperature": 0.7,
                "max_tokens": 800
            },
            "summary": {
                "prompt": SUMMARY_PROMPT,
                "temperature": 0.5,
                "max_tokens": 400
            },
            "discussion_questions": {
                "prompt": DISCUSSION_PROMPT,
                "temperature": 0.7,
                "max_tokens": 600
            }
        },
        "admin": {
            "whats_on": {
                "prompt": WHATS_ON_PROMPT,
                "temperature": 0.5,
                "max_tokens": 500
            }
        }
    }

    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://fapjxekuyckurahbtvrt.supabase.co")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "***REMOVED***")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "***REMOVED***")
    # Storage Settings
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "videos")
    STORAGE_PATH_PREFIX: str = "clients"  # Base path for all client files
    
    # Admin/Testing Settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "jared.johnston@me.com")  # Change this to your email
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, staging, production

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

settings = Settings() 