import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Request, status
from app.config.settings import settings
from app.models.schemas import (
    TranscriptionRequest,
    TranscriptionResponse,
    AsyncTranscriptionResponse,
    CallbackResponse
)
from app.services.deepgram_service import deepgram_service
from app.services.classifier_service import classifier_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=TranscriptionResponse)
async def transcribe_video(request: TranscriptionRequest):
    """
    Transcribe a video from URL and classify its segments
    """
    try:
        logger.info(f"Received transcription request for URL: {request.video_url}")
        
        # Get transcription from Deepgram
        result = await deepgram_service.transcribe_file_async(
            request.video_url,
            request.mime_type,
            settings.CALLBACK_URL
        )
        
        return TranscriptionResponse(
            request_id=result["request_id"],
            status="processing",
            metadata={
                "video_url": request.video_url
            }
        )
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed: {str(e)}"
        )

@router.post("/upload", response_model=AsyncTranscriptionResponse)
async def transcribe_upload(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio/video file using Deepgram API with streaming support
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
        
        # Create async generator for streaming file content
        async def file_stream():
            while chunk := await file.read(settings.CHUNK_SIZE):
                yield chunk
        
        # Start async transcription with streaming
        result = await deepgram_service.transcribe_file_async(
            file=file_stream(),
            mime_type=file.content_type,
            callback_url=settings.CALLBACK_URL,
            file_size=file_size  # Pass file size for better handling
        )
        
        logger.info(f"Async transcription request accepted. Request ID: {result['request_id']}")
        
        return AsyncTranscriptionResponse(
            message="Transcription started successfully",
            request_id=result["request_id"],
            callback_url=settings.CALLBACK_URL,
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

@router.post("/callback", response_model=CallbackResponse)
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
        
        # Classify the segments
        segments = await classifier_service.classify_segments(utterances)
        
        # Here you would typically:
        # 1. Store the results in a database
        # 2. Notify any waiting clients
        
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