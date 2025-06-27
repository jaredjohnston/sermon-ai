import asyncio
import logging
from datetime import datetime, UTC
from typing import List, Optional

from supabase import create_client
from app.config.settings import settings
from app.services.audio_extraction_service import audio_extraction_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioCleanupService:
    """Service for cleaning up expired audio files based on retention policy"""
    
    def __init__(self):
        # Initialize Supabase client for database operations
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    
    async def cleanup_expired_audio_files(self) -> dict:
        """
        Find and cleanup audio files that have exceeded the retention period
        
        Returns:
            Dict with cleanup statistics
        """
        try:
            logger.info(f"🧹 Starting cleanup of audio files older than {settings.AUDIO_RETENTION_DAYS} days")
            
            # Find transcripts with expired audio files
            expired_transcripts = await self._find_expired_audio_transcripts()
            
            if not expired_transcripts:
                logger.info("✅ No expired audio files found")
                return {
                    "status": "success",
                    "cleaned_up": 0,
                    "failed": 0,
                    "message": "No expired audio files found"
                }
            
            logger.info(f"📂 Found {len(expired_transcripts)} audio files to cleanup")
            
            # Cleanup each expired audio file
            cleaned_up = 0
            failed = 0
            
            for transcript in expired_transcripts:
                try:
                    await self._cleanup_transcript_audio(transcript)
                    cleaned_up += 1
                except Exception as e:
                    logger.error(f"❌ Failed to cleanup audio for transcript {transcript['id']}: {str(e)}")
                    failed += 1
            
            logger.info(f"🎯 Cleanup completed: {cleaned_up} cleaned up, {failed} failed")
            
            return {
                "status": "success",
                "cleaned_up": cleaned_up,
                "failed": failed,
                "message": f"Cleaned up {cleaned_up} expired audio files"
            }
            
        except Exception as e:
            logger.error(f"💥 Error during audio cleanup: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "cleaned_up": 0,
                "failed": 0,
                "message": f"Cleanup failed: {str(e)}"
            }
    
    async def _find_expired_audio_transcripts(self) -> List[dict]:
        """
        Find transcripts with audio files that have exceeded retention period
        
        Returns:
            List of transcript records with expired audio files
        """
        try:
            # Query transcripts with scheduled cleanup dates that have passed
            current_time = datetime.now(UTC).isoformat()
            
            # Use PostgreSQL JSON operators to query metadata
            response = self.supabase.table("transcripts").select(
                "id, metadata, created_by"
            ).filter(
                "status", "eq", "completed"
            ).filter(
                "metadata->>audio_cleanup_scheduled", "lte", current_time
            ).is_(
                "metadata->>audio_storage_path", "not.null"
            ).execute()
            
            if response.data:
                logger.info(f"📋 Found {len(response.data)} transcripts with expired audio files")
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error querying expired audio transcripts: {str(e)}")
            return []
    
    async def _cleanup_transcript_audio(self, transcript: dict) -> None:
        """
        Cleanup audio file for a specific transcript
        
        Args:
            transcript: Transcript record with metadata containing audio_storage_path
        """
        try:
            metadata = transcript.get("metadata", {})
            audio_storage_path = metadata.get("audio_storage_path")
            
            if not audio_storage_path:
                logger.warning(f"⚠️ No audio storage path found for transcript {transcript['id']}")
                return
            
            # Delete the audio file from storage
            await audio_extraction_service.cleanup_audio_file(audio_storage_path)
            
            # Update transcript metadata to remove cleanup schedule and audio path
            updated_metadata = metadata.copy()
            updated_metadata.pop("audio_cleanup_scheduled", None)
            updated_metadata.pop("audio_storage_path", None)
            updated_metadata["audio_cleaned_up_at"] = datetime.now(UTC).isoformat()
            
            # Update the transcript record
            update_response = self.supabase.table("transcripts").update({
                "metadata": updated_metadata
            }).eq("id", transcript["id"]).execute()
            
            if update_response.data:
                logger.info(f"✅ Successfully cleaned up audio for transcript {transcript['id']}")
            else:
                logger.warning(f"⚠️ Failed to update transcript metadata for {transcript['id']}")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up audio for transcript {transcript['id']}: {str(e)}")
            raise
    
    async def get_cleanup_statistics(self) -> dict:
        """
        Get statistics about audio files and cleanup schedule
        
        Returns:
            Dict with statistics about audio files
        """
        try:
            # Count total audio files awaiting cleanup
            current_time = datetime.now(UTC).isoformat()
            
            # Files with cleanup scheduled (not yet expired)
            pending_response = self.supabase.table("transcripts").select(
                "id", count="exact"
            ).filter(
                "status", "eq", "completed"
            ).filter(
                "metadata->>audio_cleanup_scheduled", "gt", current_time
            ).is_(
                "metadata->>audio_storage_path", "not.null"
            ).execute()
            
            # Files with cleanup scheduled (expired)
            expired_response = self.supabase.table("transcripts").select(
                "id", count="exact"
            ).filter(
                "status", "eq", "completed"
            ).filter(
                "metadata->>audio_cleanup_scheduled", "lte", current_time
            ).is_(
                "metadata->>audio_storage_path", "not.null"
            ).execute()
            
            # Files already cleaned up
            cleaned_response = self.supabase.table("transcripts").select(
                "id", count="exact"
            ).is_(
                "metadata->>audio_cleaned_up_at", "not.null"
            ).execute()
            
            return {
                "status": "success",
                "statistics": {
                    "pending_cleanup": pending_response.count or 0,
                    "expired_ready_for_cleanup": expired_response.count or 0,
                    "already_cleaned": cleaned_response.count or 0,
                    "retention_days": settings.AUDIO_RETENTION_DAYS
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cleanup statistics: {str(e)}")
            return {
                "status": "error",
                "statistics": {},
                "message": f"Failed to get statistics: {str(e)}"
            }


# Singleton instance
audio_cleanup_service = AudioCleanupService()