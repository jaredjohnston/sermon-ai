import logging
from typing import BinaryIO, Dict, Any, AsyncGenerator, Union
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource
)
from app.config.settings import settings

logger = logging.getLogger(__name__)

class DeepgramService:
    """Service for handling Deepgram transcription operations"""
    
    def __init__(self):
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
    
    async def transcribe_file_async(
        self,
        file: Union[AsyncGenerator[bytes, None], BinaryIO],
        mime_type: str,
        callback_url: str,
        file_size: int = None
    ) -> Dict[str, Any]:
        """
        Transcribe a file asynchronously using Deepgram with streaming support
        
        Args:
            file: The file to transcribe (either async generator for streaming or file object)
            mime_type: The MIME type of the file
            callback_url: URL where Deepgram should send results
            file_size: Optional file size for better handling of large files
            
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
            
            # Handle streaming vs direct file upload
            if isinstance(file, AsyncGenerator):
                source = FileSource(
                    stream=file,
                    mimetype=mime_type,
                    buffer_size=settings.CHUNK_SIZE
                )
            else:
                source = {
                    "buffer": file,
                    "mimetype": mime_type
                }
            
            # Start async transcription
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