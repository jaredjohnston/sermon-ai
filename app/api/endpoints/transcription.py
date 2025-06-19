import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Request, Depends
from app.config.settings import settings
from app.services.deepgram_service import deepgram_service
from app.services.supabase_service import supabase_service
from app.services.validation_service import validation_service
from app.middleware.auth import get_current_user
from app.models.schemas import User, VideoCreate, TranscriptCreate
from datetime import datetime, UTC
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def transcribe_upload(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe uploaded audio/video file using Deepgram API
    Requires authentication
    """
    try:
        logger.info(f"Received transcription request for file: {file.filename} from user: {current_user.email}")
        
        # Get user's client
        client = await supabase_service.get_user_client(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to upload files"
            )
        
        # STEP 1: Validate file BEFORE any processing  
        logger.info(f"Validating file for transcription: {file.filename}")
        validation_result = validation_service.validate_complete_for_transcription(file)
        
        if not validation_result.is_valid:
            logger.warning(f"File validation failed: {validation_result.error_message}")
            raise validation_service.convert_to_http_exception(validation_result)
        
        # Extract validated file info
        file_size = validation_result.file_info["size_bytes"]
        file_size_mb = validation_result.file_info["size_mb"]
        logger.info(f"File validation passed: {validation_result.file_info}")
        
        try:
            # STEP 2: Create database records
            logger.info(f"Creating video record for {file.filename} ({file_size_mb}MB)")
            
            # Create storage path using settings prefix
            storage_path = f"{settings.STORAGE_PATH_PREFIX}/{client.id}/videos/{file.filename}"
            
            # Create video record first
            video = await supabase_service.create_video(
                VideoCreate(
                    filename=file.filename,
                    content_type=file.content_type,
                    size_bytes=file_size,
                    storage_path=storage_path,
                    client_id=client.id,
                    metadata=validation_result.file_info  # Store validation results
                ),
                current_user.id
            )
            logger.info(f"Video record created: {video.id}")
            
            # STEP 3: Upload file to storage
            logger.info(f"Uploading {file_size_mb}MB file to storage (this may take a moment)...")
            supabase_signed_url = await deepgram_service.upload_to_supabase(
                file=file.file,
                content_type=file.content_type,
                storage_path=storage_path
            )
            logger.info(f"File uploaded successfully, signed URL generated")
            
            # STEP 4: Start AI transcription
            logger.info(f"Starting AI transcription with Deepgram...")
            result = await deepgram_service.transcribe_from_url(supabase_signed_url)
            logger.info(f"Transcription job started with request_id: {result.get('request_id')}")
            
            # STEP 5: Create transcript tracking record
            transcript = await supabase_service.create_transcript(
                TranscriptCreate(
                    video_id=video.id,
                    client_id=client.id,
                    status="processing",
                    request_id=result.get("request_id")
                ),
                current_user.id
            )
            logger.info(f"Transcript record created: {transcript.id}")
            
            # SUCCESS: Return comprehensive status information
            return {
                "success": True,
                "message": "File uploaded and transcription started successfully",
                "video_id": str(video.id),
                "transcript_id": str(transcript.id),
                "request_id": result.get("request_id"),
                "status": "processing",
                "file_info": {
                    "filename": file.filename,
                    "size_mb": file_size_mb,
                    "content_type": file.content_type
                },
                "next_steps": {
                    "description": "Transcription is processing in the background",
                    "estimated_time": f"~{max(2, int(file_size_mb / 50))} minutes",  # Rough estimate
                    "callback_url": result.get("callback_url")
                }
            }
            
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

@router.get("/videos")
async def list_videos(current_user: User = Depends(get_current_user)):
    """List all videos for the current user's client"""
    try:
        # Get user's client
        client = await supabase_service.get_user_client(current_user.id)
        if not client:
            return []
            
        videos = await supabase_service.get_client_videos(client.id)
        return videos
    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list videos: {str(e)}"
        )

@router.get("/status/{transcript_id}")
async def get_transcription_status(
    transcript_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the current status of a transcription job"""
    try:
        from uuid import UUID
        transcript_uuid = UUID(transcript_id)
        
        # This will be implemented when we add the get_transcript method
        # For now, return a placeholder
        return {
            "transcript_id": transcript_id,
            "status": "processing",
            "message": "Status checking will be implemented in next version"
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transcript ID format"
        )
    except Exception as e:
        logger.error(f"Error getting transcription status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transcription status"
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
            "processed_at": datetime.now(UTC).isoformat()
        }
            
    except Exception as e:
        logger.error(f"Error processing Deepgram callback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process callback: {str(e)}"
        )
