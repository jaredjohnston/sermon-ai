import logging
from enum import Enum
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class FileCategory(Enum):
    """Enumeration of supported file categories for processing"""
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"

class FileTypeService:
    """Service for detecting and categorizing file types based on MIME type"""
    
    @staticmethod
    def detect_file_category(content_type: str) -> FileCategory:
        """
        Detect the file category based on MIME type
        
        Args:
            content_type: The MIME type of the file (e.g., "audio/mpeg", "video/mp4")
            
        Returns:
            FileCategory enum value indicating the detected category
        """
        if not content_type:
            logger.warning("No content type provided for file category detection")
            return FileCategory.UNKNOWN
        
        # Normalize content type (remove charset, etc.)
        normalized_type = content_type.split(';')[0].strip().lower()
        
        # Check against audio types
        if normalized_type in settings.ALLOWED_AUDIO_TYPES:
            logger.info(f"Detected audio file: {normalized_type}")
            return FileCategory.AUDIO
        
        # Check against video types
        if normalized_type in settings.ALLOWED_VIDEO_TYPES:
            logger.info(f"Detected video file: {normalized_type}")
            return FileCategory.VIDEO
        
        # Check against document types
        if normalized_type in settings.ALLOWED_DOCUMENT_TYPES:
            logger.info(f"Detected document file: {normalized_type}")
            return FileCategory.DOCUMENT
        
        # Unknown/unsupported type
        logger.warning(f"Unknown or unsupported file type: {normalized_type}")
        return FileCategory.UNKNOWN
    
    @staticmethod
    def is_audio_file(content_type: str) -> bool:
        """Check if the file is an audio file"""
        return FileTypeService.detect_file_category(content_type) == FileCategory.AUDIO
    
    @staticmethod
    def is_video_file(content_type: str) -> bool:
        """Check if the file is a video file"""
        return FileTypeService.detect_file_category(content_type) == FileCategory.VIDEO
    
    @staticmethod
    def is_document_file(content_type: str) -> bool:
        """Check if the file is a document file"""
        return FileTypeService.detect_file_category(content_type) == FileCategory.DOCUMENT
    
    @staticmethod
    def get_processing_requirements(content_type: str) -> dict:
        """
        Get processing requirements based on file type
        
        Returns:
            Dictionary with processing flags and requirements
        """
        category = FileTypeService.detect_file_category(content_type)
        
        if category == FileCategory.AUDIO:
            return {
                "needs_audio_extraction": False,
                "needs_video_upload": False,
                "needs_text_extraction": False,
                "supports_transcription": True,
                "processing_type": "direct_audio"
            }
        elif category == FileCategory.VIDEO:
            return {
                "needs_audio_extraction": True,
                "needs_video_upload": True,
                "needs_text_extraction": False,
                "supports_transcription": True,
                "processing_type": "video_with_audio_extraction"
            }
        elif category == FileCategory.DOCUMENT:
            return {
                "needs_audio_extraction": False,
                "needs_video_upload": False,
                "needs_text_extraction": True,
                "supports_transcription": False,
                "processing_type": "document_text_extraction"
            }
        else:
            return {
                "needs_audio_extraction": False,
                "needs_video_upload": False,
                "needs_text_extraction": False,
                "supports_transcription": False,
                "processing_type": "unsupported"
            }

# Create a singleton instance for easy importing
file_type_service = FileTypeService()