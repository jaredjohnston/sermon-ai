import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Request, status
from app.config.settings import settings
from app.models.schemas import AsyncTranscriptionResponse, CallbackResponse
from app.services.deepgram_service import deepgram_service
from app.services.openai_service import openai_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/transcribe", response_model=AsyncTranscriptionResponse)
async def transcribe_media(file: UploadFile = File(...)):
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
        
        # Your callback URL where Deepgram will send results
        callback_url = "https://your-domain.com/api/v1/transcribe/callback"
        
        # Start async transcription
        result = await deepgram_service.transcribe_file_async(
            file=file.file,
            mime_type=file.content_type,
            callback_url=callback_url
        )
        
        logger.info(f"Async transcription request accepted. Request ID: {result['request_id']}")
        
        return AsyncTranscriptionResponse(
            message="Transcription started successfully",
            request_id=result["request_id"],
            callback_url=callback_url,
            filename=file.filename,
            size=f"{file_size/1024/1024:.2f} MB",
            content_type=file.content_type
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed: {str(e)}"
        )

@router.post("/transcribe/callback", response_model=CallbackResponse)
async def deepgram_callback(request: Request):
    """
    Handle callbacks from Deepgram with transcription results
    """
    try:
        # Get the callback data
        callback_data = await request.json()
        
        # Extract the transcription results
        results = callback_data.get("results", {})
        request_id = callback_data.get("request_id")
        
        logger.info(f"Received callback for request ID: {request_id}")
        
        if not results or "utterances" not in results:
            logger.error("Unexpected callback format from Deepgram")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid callback data format"
            )
        
        # Process the results
        utterances = results["utterances"]
        
        # Here you would typically:
        # 1. Store the results in a database
        # 2. Notify any waiting clients
        # 3. Trigger any post-processing
        
        return CallbackResponse(
            status="success",
            message="Callback processed successfully",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing callback: {str(e)}"
        ) 