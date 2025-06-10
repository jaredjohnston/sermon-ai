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
        
        # Initialize Supabase client
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
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
        
    async def upload_to_supabase(self, file: BinaryIO, content_type: str) -> str:
        """Upload file to Supabase Storage and get signed URL"""
        try:
            # Create a unique filename
            filename = f"transcription_{asyncio.get_event_loop().time()}.mp4"
            logger.info(f"Attempting to upload file to Supabase with filename: {filename}")
            
            # Get current position to restore later
            current_pos = file.tell()
            # Reset to start of file
            file.seek(0)
            # Read file content
            file_content = file.read()
            # Reset file position
            file.seek(current_pos)
            
            # Upload file to 'videos-test' bucket with explicit content type
            logger.info("Starting file upload to Supabase 'videos-test' bucket...")
            response = self.supabase.storage \
                .from_('videos-test') \
                .upload(
                    filename,      # path
                    file_content,  # file content as bytes
                    file_options={
                        "content-type": content_type  # Use passed content type
                    }
                )
            logger.info(f"File upload response from Supabase: {response}")
            
            # Get signed URL with token
            signed_url_response = self.supabase.storage \
                .from_('videos-test') \
                .create_signed_url(filename, 60 * 60 * 24)  # 24 hour expiry
            
            # Extract the signed URL with token
            signed_url = signed_url_response['signedURL']
            logger.info(f"Generated Supabase signed URL: {signed_url}")
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {str(e)}", exc_info=True)
            raise

    async def transcribe_file(self, file: BinaryIO, content_type: str = None) -> Dict[str, Any]:
        """
        Transcribe a file by first uploading to Supabase Storage,
        then using the public URL with Deepgram's prerecorded API

        Args:
            file: File-like object containing the audio/video
            content_type: The content type of the file (e.g. video/mp4)
            
        Returns:
            Dict containing:
                - request_id: Deepgram's request ID for tracking
                - callback_url: The URL where results will be sent
                - status: Current status (always "processing" initially)
            
        Raises:
            ValueError: If file contains no audio streams
        """
        # Validate audio before proceeding
        if not self._validate_audio(file):
            raise ValueError("File contains no audio streams. Cannot transcribe.")
        
        try:
            # Upload to Supabase and get public URL
            source_url = await self.upload_to_supabase(file, content_type or "video/mp4")
            
            # Configure transcription options
            options = PrerecordedOptions(
                model="nova-3",
                smart_format=True,
                punctuate=True,
                diarize=True,
                callback=settings.CALLBACK_URL
            )

            # Start the transcription job using the URL
            logger.info(f"Callback URL configured as: {settings.CALLBACK_URL}")
            logger.info(f"Transcription options: {options}")
            logger.info(f"Source URL: {source_url}")
            
            try:
                # Call Deepgram API using asyncrest namespace (matching test file)
                response = await self.client.listen.asyncrest.v("1").transcribe_url(
                    {"url": source_url},  # Pass as dict with 'url' key
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

# Export a singleton instance
deepgram_service = DeepgramService()
