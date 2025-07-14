import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Tuple

import ffmpeg
from fastapi import UploadFile

from supabase import create_client
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioExtractionError(Exception):
    """Raised when audio extraction fails"""
    pass


class AudioExtractionService:
    """Service for extracting audio from video files and uploading to Supabase"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "sermon_ai_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize Supabase client for direct storage operations
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    
    async def save_stream_to_temp_file(self, video_stream: UploadFile) -> Path:
        """
        Save video stream to temporary file for independent processing
        
        Args:
            video_stream: FastAPI UploadFile containing video data
            
        Returns:
            Path to temporary video file
            
        Raises:
            AudioExtractionError: If saving stream fails
        """
        temp_video_path = self.temp_dir / f"temp_video_{uuid.uuid4().hex}"
        
        try:
            # Ensure we start from the beginning of the stream
            await video_stream.seek(0)
            
            logger.info(f"Saving video stream to temporary file for concurrent processing...")
            
            with open(temp_video_path, "wb") as temp_file:
                # Read video stream in chunks to handle large files
                chunk_size = 8 * 1024 * 1024  # 8MB chunks
                total_bytes = 0
                while chunk := await video_stream.read(chunk_size):
                    temp_file.write(chunk)
                    total_bytes += len(chunk)
            
            # Verify the file was written correctly
            if temp_video_path.stat().st_size == 0:
                raise AudioExtractionError("Failed to write video data to temporary file")
            
            logger.info(f"Video stream saved to temp file: {temp_video_path.name} ({total_bytes} bytes)")
            return temp_video_path
            
        except Exception as e:
            # Cleanup on failure
            if temp_video_path.exists():
                temp_video_path.unlink()
            raise AudioExtractionError(f"Failed to save video stream: {str(e)}")

    async def extract_and_upload_audio(
        self, 
        video_stream: UploadFile,
        client_id: str,
        video_id: str
    ) -> Tuple[str, str, Path]:
        """
        Extract audio from video stream and immediately upload to Supabase
        
        Args:
            video_stream: FastAPI UploadFile containing video data
            client_id: Client ID for storage path
            video_id: Video ID for file naming
            
        Returns:
            Tuple of (audio_storage_path, signed_url_for_deepgram, temp_video_path)
            
        Raises:
            AudioExtractionError: If extraction or upload fails
        """
        audio_filename = f"audio_{video_id}_{uuid.uuid4().hex[:8]}.wav"
        audio_storage_path = f"{settings.STORAGE_PATH_PREFIX}/{client_id}/audio/{audio_filename}"
        temp_audio_path = self.temp_dir / audio_filename
        temp_video_path = None
        
        try:
            # STEP 1: Save stream to temporary file (single read, no conflicts)
            logger.info(f"Starting audio extraction for video_id: {video_id}")
            temp_video_path = await self.save_stream_to_temp_file(video_stream)
            
            # STEP 2: Extract audio from the saved file
            await self._extract_audio_ffmpeg(temp_video_path, temp_audio_path)
            
            # STEP 3: Immediately upload audio to Supabase 
            logger.info(f"Immediately uploading extracted audio to Supabase: {audio_storage_path}")
            
            with open(temp_audio_path, "rb") as audio_file:
                audio_content = audio_file.read()
                
                response = self.supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                    audio_storage_path,
                    audio_content,
                    file_options={"content-type": "audio/wav"}
                )
                
                if hasattr(response, 'error') and response.error:
                    raise AudioExtractionError(f"Supabase upload failed: {response.error}")
            
            # STEP 4: Generate signed URL for Deepgram
            signed_url_response = self.supabase.storage.from_(settings.STORAGE_BUCKET).create_signed_url(
                audio_storage_path, 
                60 * 60 * 24  # 24 hours
            )
            signed_url = signed_url_response['signedURL']
            
            logger.info(f"Audio extraction and upload completed: {audio_filename}")
            # Return temp_video_path for video upload to use
            return audio_storage_path, signed_url, temp_video_path
            
        except Exception as e:
            logger.error(f"Audio extraction and upload failed: {str(e)}")
            # Cleanup temp video file on error
            if temp_video_path and temp_video_path.exists():
                temp_video_path.unlink()
            raise AudioExtractionError(f"Failed to extract and upload audio: {str(e)}")
            
        finally:
            # Cleanup audio temp file (but keep video temp file for video upload)
            if temp_audio_path.exists():
                temp_audio_path.unlink()
    
    def cleanup_temp_video_file(self, temp_video_path: Path) -> None:
        """
        Clean up temporary video file after video upload completes
        
        Args:
            temp_video_path: Path to temporary video file to delete
        """
        try:
            if temp_video_path and temp_video_path.exists():
                temp_video_path.unlink()
                logger.info(f"Cleaned up temporary video file: {temp_video_path.name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary video file {temp_video_path}: {str(e)}")
    
    async def _extract_audio_ffmpeg(self, input_path: Path, output_path: Path) -> None:
        """
        Extract audio using FFmpeg with WAV format optimized for Deepgram
        
        Args:
            input_path: Path to input video file
            output_path: Path where audio file should be saved
        """
        try:
            # Run FFmpeg extraction in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_ffmpeg_extraction,
                str(input_path),
                str(output_path)
            )
        except Exception as e:
            raise AudioExtractionError(f"FFmpeg extraction failed: {str(e)}")
    
    def _run_ffmpeg_extraction(self, input_path: str, output_path: str) -> None:
        """
        Synchronous FFmpeg extraction - runs in thread executor
        
        Uses WAV format optimized for Deepgram:
        - WAV format (better than MP3 for speech recognition)
        - 16-bit PCM encoding
        - 44.1kHz sample rate  
        - Stereo (2 channels) - better quality than mono
        """
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    vn=None,  # No video
                    acodec='pcm_s16le',  # 16-bit PCM
                    ar=44100,  # 44.1kHz sample rate (higher quality than 16kHz)
                    ac=2,  # Stereo for better quality
                    f='wav'  # WAV format
                )
                .overwrite_output()
                .run(quiet=True, capture_stdout=True)
            )
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise AudioExtractionError(f"FFmpeg command failed: {error_message}")
    
    async def _extract_audio_streaming(self, video_url: str, output_path: Path) -> None:
        """
        Extract audio directly from HTTP URL using FFmpeg streaming
        This eliminates the need to download the video file first
        
        Args:
            video_url: HTTP URL to video file (e.g., Supabase signed URL)
            output_path: Path where audio file should be saved
            
        Raises:
            AudioExtractionError: If streaming extraction fails
        """
        try:
            # Run FFmpeg extraction in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_ffmpeg_streaming,
                video_url,
                str(output_path)
            )
        except Exception as e:
            raise AudioExtractionError(f"FFmpeg streaming extraction failed: {str(e)}")
    
    def _run_ffmpeg_streaming(self, video_url: str, output_path: str) -> None:
        """
        Synchronous FFmpeg streaming extraction - runs in thread executor
        Uses direct HTTP URL input to avoid downloading video file
        
        Args:
            video_url: HTTP URL to video file
            output_path: Path where audio file should be saved
        """
        try:
            (
                ffmpeg
                .input(video_url)  # Direct HTTP URL input
                .output(
                    output_path,
                    vn=None,  # No video
                    acodec='pcm_s16le',  # 16-bit PCM
                    ar=44100,  # 44.1kHz sample rate
                    ac=2,  # Stereo for better quality
                    f='wav'  # WAV format
                )
                .overwrite_output()
                .run(quiet=True, capture_stdout=True)
            )
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise AudioExtractionError(f"FFmpeg streaming command failed: {error_message}")
    
    async def cleanup_audio_file(self, audio_storage_path: str) -> None:
        """
        Clean up audio file from Supabase storage after successful transcription
        
        Args:
            audio_storage_path: Storage path of audio file to delete
        """
        try:
            response = self.supabase.storage.from_(settings.STORAGE_BUCKET).remove([audio_storage_path])
            
            if hasattr(response, 'error') and response.error:
                logger.warning(f"Supabase delete error for {audio_storage_path}: {response.error}")
            else:
                logger.info(f"Cleaned up audio file from storage: {audio_storage_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup audio file {audio_storage_path}: {str(e)}")
    
    async def extract_and_upload_audio_from_storage(
        self,
        video_storage_path: str,
        client_id: str,
        media_id: str
    ) -> Tuple[str, str]:
        """
        Extract audio from video file already stored in Supabase Storage
        Downloads video, extracts audio, uploads audio back to storage
        
        Args:
            video_storage_path: Storage path of video file in Supabase
            client_id: Client ID for storage path
            media_id: Media ID for file naming
            
        Returns:
            Tuple of (audio_storage_path, audio_signed_url)
            
        Raises:
            AudioExtractionError: If extraction or upload fails
        """
        from app.utils.http_client import http_client
        
        temp_video_path = None
        temp_audio_path = None
        
        try:
            logger.info(f"🎬 Extracting audio from stored video: {video_storage_path}")
            
            # Get signed URL to download the video
            video_signed_url = self.supabase.storage.from_(settings.STORAGE_BUCKET).create_signed_url(video_storage_path, 3600)
            if hasattr(video_signed_url, 'error') and video_signed_url.error:
                raise AudioExtractionError(f"Failed to create video signed URL: {video_signed_url.error}")
            
            video_url = video_signed_url.get('signedURL')
            
            # Create temporary files
            audio_filename = f"audio_{media_id}_{uuid.uuid4().hex[:8]}.wav"
            temp_video_path = self.temp_dir / f"temp_video_{media_id}.tmp"
            temp_audio_path = self.temp_dir / f"temp_audio_{media_id}.wav"
            
            # Try streaming extraction first (faster, no temp video file)
            logger.info(f"🎵 Attempting streaming audio extraction...")
            
            try:
                await self._extract_audio_streaming(video_url, temp_audio_path)
                logger.info(f"✅ Streaming extraction successful")
            except Exception as streaming_error:
                logger.warning(f"⚠️ Streaming extraction failed: {streaming_error}")
                logger.info(f"📥 Falling back to download method...")
                
                # Fallback: Download video file then extract
                total_bytes = await http_client.download_file(
                    url=video_url,
                    file_path=str(temp_video_path),
                    chunk_size=8192
                )
                logger.info(f"📥 Downloaded video ({total_bytes} bytes)")
                
                # Extract audio using existing FFmpeg logic
                logger.info(f"🎵 Extracting audio from downloaded file...")
                await self._extract_audio_ffmpeg(temp_video_path, temp_audio_path)
            
            # Upload extracted audio back to storage
            audio_storage_path = f"{settings.STORAGE_PATH_PREFIX}/{client_id}/audio/{audio_filename}"
            
            logger.info(f"📤 Uploading extracted audio to storage...")
            with open(temp_audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            upload_response = self.supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                audio_storage_path,
                audio_data,
                file_options={"content-type": "audio/wav"}
            )
            
            if hasattr(upload_response, 'error') and upload_response.error:
                raise AudioExtractionError(f"Failed to upload audio: {upload_response.error}")
            
            # Generate signed URL for Deepgram
            audio_signed_response = self.supabase.storage.from_(settings.STORAGE_BUCKET).create_signed_url(audio_storage_path, 3600)
            if hasattr(audio_signed_response, 'error') and audio_signed_response.error:
                raise AudioExtractionError(f"Failed to create audio signed URL: {audio_signed_response.error}")
            
            audio_signed_url = audio_signed_response.get('signedURL')
            
            logger.info(f"✅ Audio extraction completed: {audio_storage_path}")
            return audio_storage_path, audio_signed_url
            
        except Exception as e:
            logger.error(f"❌ Storage-to-storage audio extraction failed: {str(e)}", exc_info=True)
            raise AudioExtractionError(f"Audio extraction from storage failed: {str(e)}")
            
        finally:
            # Cleanup temporary files
            if temp_video_path and temp_video_path.exists():
                try:
                    temp_video_path.unlink()
                    logger.info(f"🧹 Cleaned up temp video: {temp_video_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp video: {e}")
            
            if temp_audio_path and temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                    logger.info(f"🧹 Cleaned up temp audio: {temp_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp audio: {e}")


# Singleton instance
audio_extraction_service = AudioExtractionService()