import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.config.settings import settings
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

class AudioProcessingError(Exception):
    """Raised when audio processing fails"""
    pass

class AudioService:
    """Service for direct audio file processing and upload"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "sermon_ai_audio"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def save_audio_stream_to_temp_file(self, audio_stream: UploadFile, filename: str = None) -> Path:
        """
        Save audio stream to temporary file for processing
        
        Args:
            audio_stream: FastAPI UploadFile containing audio data
            filename: Optional custom filename (defaults to generated UUID)
            
        Returns:
            Path to temporary audio file
            
        Raises:
            AudioProcessingError: If saving stream fails
        """
        try:
            # Generate temp filename if not provided
            if not filename:
                import uuid
                filename = f"audio_{uuid.uuid4().hex}.tmp"
            
            temp_file_path = self.temp_dir / filename
            
            # Save uploaded file to temporary location
            logger.info(f"Saving audio stream to temporary file: {temp_file_path}")
            
            # Reset stream position
            audio_stream.file.seek(0)
            
            # Write stream to temp file
            with open(temp_file_path, "wb") as temp_file:
                content = await audio_stream.read()
                temp_file.write(content)
            
            # Reset stream position for potential reuse
            audio_stream.file.seek(0)
            
            logger.info(f"Audio stream saved successfully: {temp_file_path} ({len(content)} bytes)")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Failed to save audio stream to temp file: {str(e)}")
            raise AudioProcessingError(f"Failed to save audio stream: {str(e)}")
    
    async def upload_audio_file(
        self, 
        audio_file_path: Path, 
        storage_path: str, 
        content_type: str,
        file_size: int
    ) -> str:
        """
        Upload audio file to Supabase storage with smart routing
        
        Args:
            audio_file_path: Path to audio file on disk
            storage_path: Storage path in Supabase bucket
            content_type: MIME type of the audio file
            file_size: Size of the file in bytes
            
        Returns:
            Public URL of uploaded audio file
            
        Raises:
            AudioProcessingError: If upload fails
        """
        try:
            logger.info(f"Uploading audio file to storage: {storage_path}")
            
            # Use smart routing upload from supabase service
            public_url = await supabase_service.upload_file_from_path(
                file_path=audio_file_path,
                bucket_name=settings.STORAGE_BUCKET,
                storage_path=storage_path,
                content_type=content_type,
                file_size=file_size,
                size_threshold=settings.TUS_THRESHOLD
            )
            
            logger.info(f"Audio file uploaded successfully: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload audio file: {str(e)}")
            raise AudioProcessingError(f"Audio upload failed: {str(e)}")
    
    async def process_and_upload_audio(
        self, 
        audio_stream: UploadFile, 
        client_id: str, 
        media_id: str
    ) -> Tuple[str, str]:
        """
        Process audio file and upload to storage
        
        Args:
            audio_stream: FastAPI UploadFile containing audio data
            client_id: Client identifier for storage organization
            media_id: Media record identifier
            
        Returns:
            Tuple of (storage_path, signed_url)
            
        Raises:
            AudioProcessingError: If processing fails
        """
        temp_audio_path = None
        
        try:
            # Step 1: Save audio stream to temp file
            logger.info(f"Processing audio file for media_id: {media_id}")
            temp_audio_path = await self.save_audio_stream_to_temp_file(
                audio_stream, 
                f"audio_{media_id}.tmp"
            )
            
            # Step 2: Generate storage path
            file_extension = Path(audio_stream.filename).suffix
            storage_path = f"{settings.STORAGE_PATH_PREFIX}/{client_id}/audio/{media_id}_audio{file_extension}"
            
            # Step 3: Get file size for upload routing
            file_size = temp_audio_path.stat().st_size
            
            # Step 4: Upload to Supabase storage
            public_url = await self.upload_audio_file(
                audio_file_path=temp_audio_path,
                storage_path=storage_path,
                content_type=audio_stream.content_type,
                file_size=file_size
            )
            
            # Step 5: Generate signed URL for transcription
            from supabase import create_client
            temp_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
            signed_url_response = temp_supabase.storage.from_(settings.STORAGE_BUCKET).create_signed_url(
                storage_path, 
                60 * 60 * 24  # 24 hour expiry
            )
            signed_url = signed_url_response['signedURL']
            
            logger.info(f"Audio processing completed successfully for media_id: {media_id}")
            return storage_path, signed_url
            
        except Exception as e:
            logger.error(f"Audio processing failed for media_id {media_id}: {str(e)}")
            raise AudioProcessingError(f"Audio processing failed: {str(e)}")
            
        finally:
            # Always cleanup temp file
            if temp_audio_path and temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                    logger.info(f"Cleaned up temporary audio file: {temp_audio_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp audio file: {cleanup_error}")
    
    def cleanup_temp_audio_file(self, temp_audio_path: Path):
        """
        Clean up temporary audio file
        
        Args:
            temp_audio_path: Path to temporary audio file to remove
        """
        try:
            if temp_audio_path and temp_audio_path.exists():
                temp_audio_path.unlink()
                logger.info(f"Temporary audio file cleaned up: {temp_audio_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary audio file {temp_audio_path}: {str(e)}")

# Create a singleton instance for easy importing
audio_service = AudioService()