import logging
from typing import BinaryIO, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from pydantic import BaseModel
from app.config.settings import settings
from app.services.deepgram_service import deepgram_service

logger = logging.getLogger(__name__)

class ValidationResult(BaseModel):
    """Result of file validation"""
    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    file_info: Dict[str, Any] = {}

class ValidationService:
    """Service for validating files before processing"""
    
    @staticmethod
    def validate_basic_upload(file: UploadFile) -> ValidationResult:
        """
        Basic file validation: size, type, etc.
        Used by ALL upload endpoints regardless of processing type.
        """
        try:
            # Check file size without reading entire content
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            # Validate file size
            if file_size > settings.MAX_FILE_SIZE:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File size ({file_size/1024/1024:.2f} MB) exceeds maximum allowed size ({settings.MAX_FILE_SIZE/1024/1024/1024:.1f} GB)",
                    error_code="FILE_TOO_LARGE"
                )
            
            # Validate minimum file size (avoid empty files)
            if file_size < 1024:  # 1KB minimum
                return ValidationResult(
                    is_valid=False,
                    error_message="File is too small or empty",
                    error_code="FILE_TOO_SMALL"
                )
            
            # Check filename
            if not file.filename or len(file.filename.strip()) == 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Filename is required",
                    error_code="MISSING_FILENAME"
                )
            
            return ValidationResult(
                is_valid=True,
                file_info={
                    "size_bytes": file_size,
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "filename": file.filename,
                    "content_type": file.content_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error in basic file validation: {str(e)}")
            return ValidationResult(
                is_valid=False,
                error_message="Failed to validate file",
                error_code="VALIDATION_ERROR"
            )
    
    @staticmethod
    def validate_for_transcription(file: UploadFile) -> ValidationResult:
        """
        Transcription-specific validation: audio/video format + audio streams.
        Only call this AFTER validate_basic_upload passes.
        """
        try:
            # First check MIME type for transcription
            if file.content_type not in settings.ALLOWED_MEDIA_TYPES:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File type '{file.content_type}' not supported for transcription. Supported types: {', '.join(settings.ALLOWED_MEDIA_TYPES)}",
                    error_code="UNSUPPORTED_MEDIA_TYPE"
                )
            
            # Reset file position
            file.file.seek(0)
            
            # Use Deepgram's audio validation (the expensive check)
            logger.info(f"Validating audio streams for file: {file.filename}")
            has_audio = deepgram_service._validate_audio(file.file)
            
            if not has_audio:
                return ValidationResult(
                    is_valid=False,
                    error_message="File contains no audio streams. Cannot transcribe files without audio.",
                    error_code="NO_AUDIO_STREAMS"
                )
            
            # Reset file position after validation
            file.file.seek(0)
            
            return ValidationResult(
                is_valid=True,
                file_info={
                    "content_type": file.content_type,
                    "has_audio": True,
                    "processing_type": "transcription"
                }
            )
            
        except Exception as e:
            logger.error(f"Error in transcription validation: {str(e)}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Failed to validate file for transcription: {str(e)}",
                error_code="TRANSCRIPTION_VALIDATION_ERROR"
            )
    
    @staticmethod
    def validate_complete_for_transcription(file: UploadFile) -> ValidationResult:
        """
        Complete validation pipeline for transcription uploads.
        Combines basic + transcription-specific validation.
        """
        # Step 1: Basic validation (fast)
        basic_result = ValidationService.validate_basic_upload(file)
        if not basic_result.is_valid:
            return basic_result
        
        # Step 2: Transcription-specific validation (slower)
        transcription_result = ValidationService.validate_for_transcription(file)
        if not transcription_result.is_valid:
            return transcription_result
        
        # Combine file info from both validations
        combined_info = {**basic_result.file_info, **transcription_result.file_info}
        
        return ValidationResult(
            is_valid=True,
            file_info=combined_info
        )
    
    @staticmethod
    def convert_to_http_exception(result: ValidationResult) -> HTTPException:
        """
        Convert ValidationResult to HTTPException.
        
        USAGE PATTERN:
        - ValidationService methods return ValidationResult
        - Endpoints call this method to convert to HTTPException  
        - This keeps validation logic separate from HTTP concerns
        """
        if result.is_valid:
            raise ValueError("Cannot convert valid result to HTTPException")
        
        # Map error codes to appropriate HTTP status codes
        status_map = {
            "FILE_TOO_LARGE": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "FILE_TOO_SMALL": status.HTTP_400_BAD_REQUEST,
            "MISSING_FILENAME": status.HTTP_400_BAD_REQUEST,
            "UNSUPPORTED_MEDIA_TYPE": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "NO_AUDIO_STREAMS": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "TRANSCRIPTION_VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        http_status = status_map.get(result.error_code, status.HTTP_400_BAD_REQUEST)
        
        return HTTPException(
            status_code=http_status,
            detail=result.error_message
        )

# Create singleton instance
validation_service = ValidationService()