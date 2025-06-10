import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Request
from app.config.settings import settings
from app.services.deepgram_service import deepgram_service
from datetime import datetime
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def transcribe_upload(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio/video file using Deepgram API
    """
    try:
        logger.info(f"Received transcription request for file: {file.filename}")
        
        # Validate file type
        if file.content_type not in settings.ALLOWED_MEDIA_TYPES:
            logger.warning(f"Invalid file type received: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not supported. Supported types: {settings.ALLOWED_MEDIA_TYPES}"
            )
        
        # Get file size without reading entire content
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(f"File size exceeds limit: {file_size/1024/1024:.2f}MB")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size/1024/1024:.2f} MB) exceeds maximum allowed size (4 GB)"
            )
        
        try:
            # Reset file position after size check
            file.file.seek(0)
            
            # Get transcription with original content type
            result = await deepgram_service.transcribe_file(
                file=file.file,
                content_type=file.content_type
            )
            
            return result
            
        except Exception as e:
            # Make sure to reset file position if transcription fails
            file.file.seek(0)
            raise e
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed: {str(e)}"
        )

@router.post("/callback")
async def transcription_callback(request: Request):
    """
    Callback endpoint for Deepgram transcription results
    """
    try:
        # Get the raw JSON data from the request
        data = await request.json()
        
        # Extract and log the transcript details
        if 'results' in data and 'channels' in data['results']:
            for i, channel in enumerate(data['results']['channels']):
                logger.info(f"\nChannel {i + 1} Transcript Details:")
                if 'alternatives' in channel:
                    for j, alt in enumerate(channel['alternatives']):
                        logger.info(f"\nAlternative {j + 1}:")
                        logger.info(f"Full Transcript: {alt.get('transcript', 'No transcript available')}")
                        logger.info(f"Confidence: {alt.get('confidence', 'No confidence score')}")
                        
                        # Log individual utterances if available
                        if 'utterances' in alt:
                            logger.info("\nUtterances:")
                            for k, utterance in enumerate(alt['utterances']):
                                logger.info(f"\nUtterance {k + 1}:")
                                logger.info(f"Speaker: {utterance.get('speaker', 'Unknown')}")
                                logger.info(f"Start: {utterance.get('start', 'N/A')}s")
                                logger.info(f"End: {utterance.get('end', 'N/A')}s")
                                logger.info(f"Text: {utterance.get('transcript', 'No text')}")
                                logger.info(f"Confidence: {utterance.get('confidence', 'No confidence')}")
        else:
            logger.warning("No transcript data found in callback payload")
            
        # Log the complete raw data for debugging
        logger.info("\nComplete callback data:")
        logger.info(json.dumps(data, indent=2))
        
        return {
            "status": "success",
            "message": "Callback received and processed",
            "processed_at": datetime.utcnow().isoformat()
        }
            
    except Exception as e:
        logger.error(f"Error processing Deepgram callback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process callback: {str(e)}"
        )
