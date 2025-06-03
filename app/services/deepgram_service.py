import logging
from typing import BinaryIO, Dict, Any
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)

class DeepgramService:
    """Service for handling Deepgram transcription operations"""
    
    def __init__(self):
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
    
    async def transcribe_file_async(
        self,
        file: BinaryIO,
        mime_type: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Transcribe a file asynchronously using Deepgram
        
        Args:
            file: The file to transcribe
            mime_type: The MIME type of the file
            callback_url: URL where Deepgram should send results
            
        Returns:
            Dict containing the request ID and status
        """
        try:
            options = PrerecordedOptions(
                model="nova-3",
                smart_format=True,
                punctuate=True,
                diarize=True,
                utterances=True,
                language="en-US"
            )
            
            source = {
                "buffer": file,
                "mimetype": mime_type
            }
            
            response = await self.client.listen.rest.v("1").transcribe_file_async(
                source=source,
                options=options,
                callback_url=callback_url
            )
            
            return {
                "request_id": response.request_id,
                "status": "processing"
            }
            
        except Exception as e:
            logger.error(f"Error in Deepgram transcription: {str(e)}")
            raise

deepgram_service = DeepgramService() 