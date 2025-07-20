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
    TEST_TIMEOUT: int = 180  # 3 minutes for test operations
    
    # TUS Upload Settings
    TUS_CHUNK_SIZE: int = 6 * 1024 * 1024  # 6MB chunks (Supabase recommended)
    TUS_THRESHOLD: int = 6 * 1024 * 1024  # Use TUS for files > 6MB
    
    # Callback Settings
    CALLBACK_URL: str = os.getenv("CALLBACK_URL", "http://localhost:8000/api/v1/transcription/callback")
    
    # Webhook Security
    WEBHOOK_SECRET_TOKEN: str = os.getenv("WEBHOOK_SECRET_TOKEN", "default-webhook-secret-change-in-production")
    FASTAPI_BASE_URL: str = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
    
    # Media Types
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a",
        "audio/mpeg3", "audio/x-mpeg-3", "audio/m4a",
    ]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/mpeg", "video/webm"]
    
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "text/plain", "text/markdown", "text/html",
        "application/pdf", "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/rtf"
    ]
    ALLOWED_MEDIA_TYPES: List[str] = ALLOWED_AUDIO_TYPES + ALLOWED_VIDEO_TYPES + ALLOWED_DOCUMENT_TYPES
    
    # OpenAI Settings
    DEFAULT_MODEL: str = "gpt-4-turbo-preview"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Sermon AI"
    VERSION: str = "1.0.0"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://your-frontend-domain.com",
    ]

    # Content Generation Settings (using dynamic templates)
    DEFAULT_GENERATION_SETTINGS: Dict[str, Any] = {
        "temperature": 0.7,
        "max_tokens": 800,
        "model": "gpt-4"
    }

    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://fapjxekuyckurahbtvrt.supabase.co")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    # Storage Settings
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "sermons")  # User uploads & final outputs
    PROCESSING_BUCKET: str = os.getenv("PROCESSING_BUCKET", "sermon-processing")  # System-generated files
    STORAGE_PATH_PREFIX: str = "clients"  # Base path for all client files
    
    # Audio File Settings
    AUDIO_RETENTION_DAYS: int = int(os.getenv("AUDIO_RETENTION_DAYS", "30"))  # Keep audio files for 30 days for audit purposes
    
    # Admin/Testing Settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "jared.johnston@me.com")  # Change this to your email
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, staging, production

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

settings = Settings() 