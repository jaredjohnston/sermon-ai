import logging
import asyncio
import ffmpeg
import tempfile
from typing import Dict, Any, BinaryIO, Optional
from supabase import create_client, Client
from deepgram import DeepgramClient, PrerecordedOptions
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepgramService:
    """Service for handling Deepgram transcription"""

    def __init__(self):
        # Initialize Deepgram client
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        
        # Initialize Supabase client with service role for database operations
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        
    def _validate_audio(self, file: BinaryIO) -> bool:
        """
        Validate that the file contains at least one audio stream.
        
        Args:
            file: File-like object containing the video/audio
            
        Returns:
            bool: True if file contains audio, False otherwise
            
        Raises:
            ValueError: If file format is invalid or cannot be processed
        """
        try:
            # Save to temporary file since ffmpeg needs a file path
            with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_file:
                # Get current position to restore later
                current_pos = file.tell()
                # Reset to start of file
                file.seek(0)
                # Write to temp file
                temp_file.write(file.read())
                temp_file.flush()
                # Reset file position
                file.seek(current_pos)
                
                # Probe file for streams
                logger.info("Probing file for audio streams...")
                probe = ffmpeg.probe(temp_file.name)
                
                # Log all streams for debugging
                for stream in probe['streams']:
                    logger.info(f"Found stream: {stream.get('codec_type', 'unknown')} - {stream}")
                
                # Check for audio streams
                audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
                has_audio = len(audio_streams) > 0
                
                if not has_audio:
                    logger.error("No audio streams found in the file")
                    return False
                    
                logger.info(f"Found {len(audio_streams)} audio stream(s)")
                for stream in audio_streams:
                    logger.info(f"Audio stream details: {stream}")
                return True
                
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error while validating audio: {str(e)}")
            raise ValueError("Invalid file format or corrupted file") from e
        except Exception as e:
            logger.error(f"Unexpected error while validating audio: {str(e)}")
            raise
        
    async def upload_to_supabase(self, file: BinaryIO, content_type: str, storage_path: str) -> str:
        """Upload file to Supabase Storage and get signed URL"""
        try:
            logger.info(f"Attempting to upload file to Supabase at path: {storage_path}")
            
            # Get current position to restore later
            current_pos = file.tell()
            # Reset to start of file
            file.seek(0)
            # Read file content
            file_content = file.read()
            # Reset file position
            file.seek(current_pos)
            
            # Upload file to configured bucket with explicit content type
            logger.info(f"Starting file upload to Supabase '{settings.STORAGE_BUCKET}' bucket...")
            response = self.supabase.storage \
                .from_(settings.STORAGE_BUCKET) \
                .upload(
                    storage_path,  # Use the full storage path
                    file_content,  # file content as bytes
                    file_options={
                        "content-type": content_type  # Use passed content type
                    }
                )
            logger.info(f"File upload response from Supabase: {response}")
            
            # Get signed URL with token
            signed_url_response = self.supabase.storage \
                .from_(settings.STORAGE_BUCKET) \
                .create_signed_url(storage_path, 60 * 60 * 24)  # 24 hour expiry
            
            # Extract the signed URL with token
            signed_url = signed_url_response['signedURL']
            logger.info(f"Generated Supabase signed URL: {signed_url}")
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {str(e)}", exc_info=True)
            raise

    async def transcribe_from_url(self, signed_url: str) -> Dict[str, Any]:
        """
        Transcribe a file from a signed URL using Deepgram's prerecorded API

        Args:
            signed_url: Signed URL of the audio/video file to transcribe (e.g. from Supabase)
            
        Returns:
            Dict containing:
                - request_id: Deepgram's request ID for tracking
                - callback_url: The URL where results will be sent
                - status: Current status (always "processing" initially)
        """
        try:
            
# Configure transcription options
            options = PrerecordedOptions(
                model="nova-3",
                smart_format=True,
                punctuate=True,
                diarize=True,
                callback=settings.CALLBACK_URL
            )

            # Start the transcription job using the signed URL
            logger.info(f"Callback URL configured as: {settings.CALLBACK_URL}")
            logger.info(f"Transcription options: {options}")
            logger.info(f"Signed URL: {signed_url}")
            
            try:
                # Call Deepgram API using asyncrest namespace (matching test file)
                response = await self.client.listen.asyncrest.v("1").transcribe_url(
                    {"url": signed_url},  # Pass signed URL as dict with 'url' key
                    options=options
                )
                
                logger.info("Deepgram API Response Details:")
                logger.info(f"Response type: {type(response)}")
                logger.info(f"Response raw: {response.to_json(indent=4)}")
                
                return {
                    "request_id": response.request_id,
                    "callback_url": settings.CALLBACK_URL,
                    "status": "processing"
                }
                
            except Exception as e:
                logger.error(f"Deepgram API error details:")
                logger.error(f"Error type: {type(e)}")
                logger.error(f"Error message: {str(e)}")
                if hasattr(e, 'response'):
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")
                raise

        except Exception as e:
            logger.error(f"Error in Deepgram transcription: {e}")
            raise

    async def transcribe_file(self, file: BinaryIO, content_type: str = None, storage_path: str = None) -> Dict[str, Any]:
        """
        Transcribe a file by first uploading to Supabase Storage,
        then using the public URL with Deepgram's prerecorded API
        
        NOTE: File should already be validated before calling this method.
        Use ValidationService.validate_complete_for_transcription() first.

        Args:
            file: File-like object containing the audio/video (already validated)
            content_type: The content type of the file (e.g. video/mp4) 
            storage_path: Path where file should be stored (optional, generates default if not provided)
            
        Returns:
            Dict containing:
                - request_id: Deepgram's request ID for tracking
                - callback_url: The URL where results will be sent
                - status: Current status (always "processing" initially)
        """
        try:
            # Use provided storage_path or generate a default one
            path = storage_path or f"transcription_{asyncio.get_event_loop().time()}.mp4"
            
            # Upload to Supabase and get signed URL
            supabase_signed_url = await self.upload_to_supabase(file, content_type or "video/mp4", path)
            
            # Use the transcribe_from_url method
            return await self.transcribe_from_url(supabase_signed_url)
            
        except Exception as e:
            logger.error(f"Error in file transcription: {e}")
            raise

# Export a singleton instance
deepgram_service = DeepgramService()
