import asyncio
import logging
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Request, Depends
from app.config.settings import settings
from app.services.deepgram_service import deepgram_service
from app.services.supabase_service import supabase_service
from app.services.validation_service import validation_service
from app.services.audio_extraction_service import audio_extraction_service, AudioExtractionError
from app.services.audio_cleanup_service import audio_cleanup_service
from app.services.file_type_service import file_type_service, FileCategory
from app.services.audio_service import audio_service, AudioProcessingError
from app.middleware.auth import get_current_user, get_auth_context, AuthContext
from app.models.schemas import User, MediaCreate, VideoCreate, TranscriptCreate, PrepareUploadRequest, PrepareUploadResponse, TUSConfig
from datetime import datetime, UTC, timedelta
import json

logger = logging.getLogger(__name__)
router = APIRouter()

async def start_transcription_when_ready(transcript_id: str, audio_signed_url: str, user_id: str, access_token: str):
    """
    Background task to start Deepgram transcription
    This runs after upload completes and doesn't block the HTTP response
    """
    try:
        logger.info(f"Starting background transcription for transcript {transcript_id}")
        
        # Give upload a moment to complete if needed
        await asyncio.sleep(2)
        
        # Update status to processing
        await supabase_service.update_transcript(
            transcript_id,
            {"status": "processing"},
            user_id,
            access_token
        )
        
        # Start Deepgram transcription
        result = await deepgram_service.transcribe_from_url(audio_signed_url)
        logger.info(f"Deepgram transcription started for {transcript_id}: {result.get('request_id')}")
        
        # Update transcript with Deepgram request_id
        await supabase_service.update_transcript(
            transcript_id,
            {"request_id": result.get("request_id")},
            user_id,
            access_token
        )
        
    except Exception as e:
        logger.error(f"Background transcription failed for {transcript_id}: {str(e)}", exc_info=True)
        
        # Update transcript status to failed
        try:
            await supabase_service.update_transcript(
                transcript_id,
                {"status": "failed", "error_message": str(e)},
                user_id,
                access_token
            )
        except Exception as update_error:
            logger.error(f"Failed to update transcript status: {update_error}")


async def upload_video_from_temp_file(temp_video_path: Path, storage_path: str, file_size: int, content_type: str) -> str:
    """
    Upload video file from temporary file to Supabase storage using smart routing
    
    Returns:
        Signed URL for the uploaded video
    """
    try:
        # Use the new boring approach - upload directly from file path
        public_url = await supabase_service.upload_file_from_path(
            file_path=temp_video_path,
            bucket_name=settings.STORAGE_BUCKET,
            storage_path=storage_path,
            content_type=content_type,
            file_size=file_size,
            size_threshold=settings.TUS_THRESHOLD
        )
        
        # Generate signed URL for potential future use
        from supabase import create_client
        temp_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        signed_url_response = temp_supabase.storage.from_(settings.STORAGE_BUCKET).create_signed_url(storage_path, 60 * 60 * 24)
        signed_url = signed_url_response['signedURL']
        
        return signed_url
        
    finally:
        # Cleanup temp file after upload (always runs)
        audio_extraction_service.cleanup_temp_video_file(temp_video_path)


async def extract_and_upload_audio(file: UploadFile, client_id: str, video_id: str) -> tuple[str, str, Path]:
    """
    Extract audio from video and immediately upload to Supabase
    
    Returns:
        Tuple of (audio_storage_path, audio_signed_url, temp_video_path)
    """
    return await audio_extraction_service.extract_and_upload_audio(
        video_stream=file,
        client_id=client_id,  
        video_id=video_id
    )

@router.post("/upload/prepare")
async def prepare_upload(
    request: PrepareUploadRequest,
    auth: AuthContext = Depends(get_auth_context)
) -> PrepareUploadResponse:
    """
    Prepare a file upload by validating file type, auth, and generating presigned URL
    This replaces the synchronous upload with a prepare -> direct upload -> webhook flow
    """
    try:
        logger.info(f"Preparing upload for file: {request.filename} from user: {auth.user.email}")
        
        # 1. AUTHENTICATION & CLIENT VALIDATION
        client = await supabase_service.get_user_client(auth.user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to upload files"
            )
        
        # 2. FILE TYPE DETECTION & VALIDATION (reuse existing logic)
        logger.info(f"Validating file: {request.filename} ({request.size_bytes} bytes)")
        
        # Create a mock validation result for the metadata-only validation
        class MockFile:
            def __init__(self, filename, content_type, size):
                self.filename = filename
                self.content_type = content_type
                self.size = size
        
        mock_file = MockFile(request.filename, request.content_type, request.size_bytes)
        
        # Use existing validation logic but for metadata only
        file_category = file_type_service.detect_file_category(request.content_type)
        processing_requirements = file_type_service.get_processing_requirements(request.content_type)
        
        # Basic validation checks
        if request.size_bytes > 50 * 1024 * 1024 * 1024:  # 50GB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 50GB limit"
            )
        
        if file_category not in [FileCategory.AUDIO, FileCategory.VIDEO]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type for transcription: {file_category.value}"
            )
        
        logger.info(f"File category detected: {file_category.value}, Processing type: {processing_requirements['processing_type']}")
        
        # 3. STORAGE PATH GENERATION WITH USER CONTEXT
        storage_path = f"{settings.STORAGE_PATH_PREFIX}/{client.id}/uploads/{request.filename}"
        
        # 4. DATABASE PREPARATION - Create media record in "preparing" state
        logger.info(f"Creating media record for {request.filename}")
        media = await supabase_service.create_media(
            MediaCreate(
                filename=request.filename,
                content_type=request.content_type,
                size_bytes=request.size_bytes,
                storage_path=storage_path,
                client_id=client.id,
                metadata={
                    "file_category": file_category.value,
                    "processing_requirements": processing_requirements,
                    "upload_status": "preparing",
                    "upload_method": "direct_to_supabase"
                }
            ),
            auth.user.id
        )
        logger.info(f"Media record created: {media.id}")
        
        # 5. SMART UPLOAD URL GENERATION BASED ON FILE SIZE
        supabase_base = settings.SUPABASE_URL.rstrip('/')
        
        # Determine upload method based on file size threshold
        tus_config = None
        if request.size_bytes > settings.TUS_THRESHOLD:
            # Large file - use TUS resumable upload
            logger.info(f"Using TUS resumable upload for large file: {request.size_bytes / 1024 / 1024:.2f}MB")
            
            upload_url = f"{supabase_base}/storage/v1/upload/resumable"
            upload_headers = {
                "Authorization": f"Bearer {auth.access_token}",
                "Content-Type": request.content_type,
                "x-upsert": "true"
            }
            upload_method = "tus_resumable"
            
            # Create TUS configuration for resumable uploads
            tus_config = TUSConfig(
                upload_url=upload_url,
                headers={
                    "Authorization": f"Bearer {auth.access_token}",
                    "tus-resumable": "1.0.0",
                    "x-upsert": "true"
                },
                metadata={
                    "bucketName": settings.STORAGE_BUCKET,
                    "objectName": storage_path,
                    "contentType": request.content_type,
                    "cacheControl": "3600"
                },
                chunk_size=getattr(settings, 'TUS_CHUNK_SIZE', 6 * 1024 * 1024),
                max_retries=3,
                retry_delay=1000,
                timeout=30000,
                parallel_uploads=1
            )
            
        else:
            # Small file - use standard HTTP PUT
            logger.info(f"Using standard HTTP PUT for small file: {request.size_bytes / 1024 / 1024:.2f}MB")
            
            upload_url = f"{supabase_base}/storage/v1/object/{settings.STORAGE_BUCKET}/{storage_path}"
            upload_headers = {
                "Authorization": f"Bearer {auth.access_token}",
                "Content-Type": request.content_type,
                "x-upsert": "true"
            }
            upload_method = "http_put"
        
        logger.info(f"Upload URL generated: {upload_url}")
        logger.info(f"Upload method: {upload_method}")
        
        # 6. SUCCESS RESPONSE  
        processing_info = {
            "file_category": file_category.value,
            "processing_type": processing_requirements["processing_type"],
            "audio_extraction_needed": processing_requirements["needs_audio_extraction"],
            "video_upload_needed": processing_requirements["needs_video_upload"],
            "estimated_processing_time": f"~{max(2, int(request.size_bytes / 1024 / 1024 / 100))} minutes",
            "upload_method": upload_method
        }
        
        logger.info(f"Upload preparation successful for media {media.id} using {upload_method}")
        
        return PrepareUploadResponse(
            upload_url=upload_url,
            upload_fields=upload_headers,  # User-authenticated headers
            media_id=str(media.id),
            processing_info=processing_info,
            upload_method=upload_method,
            tus_config=tus_config,
            expires_in=3600
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Upload preparation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload preparation failed: {str(e)}"
        )

@router.post("/upload")
async def transcribe_upload(
    request: Request,
    file: UploadFile = File(...),
    auth: AuthContext = Depends(get_auth_context)
):
    """
    Transcribe uploaded audio/video file using Deepgram API
    Requires authentication
    """
    try:
        logger.info(f"Received transcription request for file: {file.filename} from user: {auth.user.email}")
        
        # Get user's client
        client = await supabase_service.get_user_client(auth.user.id)
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
        
        # STEP 1.5: Detect file type and determine processing requirements
        file_category = file_type_service.detect_file_category(file.content_type)
        processing_requirements = file_type_service.get_processing_requirements(file.content_type)
        logger.info(f"File category detected: {file_category.value}, Processing type: {processing_requirements['processing_type']}")
        
        try:
            # STEP 2: Create database records
            logger.info(f"Creating video record for {file.filename} ({file_size_mb}MB)")
            
            # Create storage path using settings prefix
            storage_path = f"{settings.STORAGE_PATH_PREFIX}/{client.id}/uploads/{file.filename}"
            
            # Create media record first
            video = await supabase_service.create_media(
                MediaCreate(
                    filename=file.filename,
                    content_type=file.content_type,
                    size_bytes=file_size,
                    storage_path=storage_path,
                    client_id=client.id,
                    metadata=validation_result.file_info  # Store validation results
                ),
                auth.user.id
            )
            logger.info(f"Media record created: {video.id}")  # Keep 'video' var for backward compatibility
            
            # STEP 3: Route to appropriate processing pipeline based on file type
            if file_category == FileCategory.AUDIO:
                logger.info(f"Processing audio file directly (no extraction needed) for {file_size_mb}MB file...")
                try:
                    # Direct audio processing - no extraction needed
                    audio_storage_path, audio_signed_url = await audio_service.process_and_upload_audio(
                        file, client.id, str(video.id)
                    )
                    logger.info(f"Audio file processed and uploaded directly")
                    
                except AudioProcessingError as e:
                    logger.error(f"Audio processing failed: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Audio processing failed: {str(e)}"
                    )
                    
            elif file_category == FileCategory.VIDEO:
                logger.info(f"Processing video file with audio extraction for {file_size_mb}MB file...")
                try:
                    # Video processing - extract audio + background video upload
                    audio_storage_path, audio_signed_url, temp_video_path = await extract_and_upload_audio(
                        file, client.id, str(video.id)
                    )
                    logger.info(f"Audio extracted from video and uploaded")
                    
                    # Start video upload in background for video files
                    video_upload_task = asyncio.create_task(
                        upload_video_from_temp_file(temp_video_path, storage_path, file_size, file.content_type),
                        name="video_upload"
                    )
                    
                except AudioExtractionError as e:
                    logger.error(f"Audio extraction failed: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Audio extraction failed: {str(e)}"
                    )
                    
            else:
                # Unsupported file type (shouldn't reach here due to validation)
                logger.error(f"Unsupported file category: {file_category.value}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type for transcription: {file_category.value}"
                )
            
            # STEP 4: Create transcript tracking record 
            transcript = await supabase_service.create_transcript(
                TranscriptCreate(
                    video_id=video.id,
                    client_id=client.id,
                    status="pending",  # Initial status - will be updated to processing when transcription starts
                    request_id=None,
                    metadata={"audio_storage_path": audio_storage_path, "audio_signed_url": audio_signed_url}
                ),
                auth.user.id,
                auth.access_token
            )
            logger.info(f"Transcript record created: {transcript.id}")
            
            # STEP 5: Start transcription in background task (don't block HTTP response)
            asyncio.create_task(
                start_transcription_when_ready(transcript.id, audio_signed_url, auth.user.id, auth.access_token),
                name=f"transcription_{transcript.id}"
            )
            logger.info(f"Background transcription task started for transcript {transcript.id}")
            
            # Return immediately - don't wait for transcription to start
            result = {"request_id": f"async_{transcript.id}", "callback_url": f"/api/v1/transcription/callback"}
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Processing failed: {str(e)}"
            )
        
        # Generate appropriate success message based on file type
        if file_category == FileCategory.AUDIO:
            success_message = "Audio file processed and transcription started immediately."
            processing_description = "Direct audio processing (no extraction needed)"
        elif file_category == FileCategory.VIDEO:
            success_message = "Audio extracted and transcription started immediately. Video upload continues in background."
            processing_description = "Audio extraction from video with background video upload"
        else:
            success_message = "File processed and transcription started."
            processing_description = "Unknown processing type"
        
        # SUCCESS: Return comprehensive status information
        return {
            "success": True,
            "message": success_message,
            "video_id": str(video.id),
            "transcript_id": str(transcript.id),
            "request_id": result.get("request_id"),
            "status": "processing",
            "file_info": {
                "filename": file.filename,
                "size_mb": file_size_mb,
                "content_type": file.content_type
            },
            "processing_info": {
                "file_category": file_category.value,
                "processing_type": processing_requirements["processing_type"],
                "audio_extraction_needed": processing_requirements["needs_audio_extraction"],
                "video_upload_needed": processing_requirements["needs_video_upload"],
                "transcription_started": True
            },
            "next_steps": {
                "description": processing_description,
                "estimated_time": f"~{max(2, int(file_size_mb / 100))} minutes",  # Faster estimate for audio
                "callback_url": result.get("callback_url")
            }
        }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed: {str(e)}"
        )

@router.get("/videos")
async def list_videos(auth: AuthContext = Depends(get_auth_context)):
    """List all media (videos, audio, documents) for the current user's client"""
    try:
        # Get user's client
        client = await supabase_service.get_user_client(auth.user.id)
        if not client:
            return []
            
        videos = await supabase_service.get_client_media(client.id, auth.access_token)
        return videos
    except Exception as e:
        logger.error(f"Error listing media: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list media: {str(e)}"
        )

@router.get("/status/{transcript_id}")
async def get_transcription_status(
    transcript_id: str,
    auth: AuthContext = Depends(get_auth_context)
):
    """Get the current status of a transcription job"""
    try:
        from uuid import UUID
        transcript_uuid = UUID(transcript_id)
        
        # Get user's client for authorization
        client = await supabase_service.get_user_client(auth.user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # Get transcript
        transcript = await supabase_service.get_transcript(transcript_uuid, auth.access_token)
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )
        
        # Check authorization - user can only access their client's transcripts
        if transcript.client_id != client.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: transcript belongs to different organization"
            )
        
        # Calculate estimated completion time for processing jobs
        estimated_completion = None
        if transcript.status == "processing":
            from datetime import datetime, timedelta, UTC
            # Rough estimate: 1 minute per MB (very conservative)
            # This would typically come from video metadata
            estimated_minutes = 5  # Default estimate
            estimated_completion = (transcript.created_at + timedelta(minutes=estimated_minutes)).isoformat()
        
        return {
            "transcript_id": str(transcript.id),
            "video_id": str(transcript.video_id),
            "status": transcript.status,
            "created_at": transcript.created_at.isoformat(),
            "updated_at": transcript.updated_at.isoformat(),
            "estimated_completion": estimated_completion,
            "error_message": transcript.error_message,
            "request_id": transcript.request_id
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transcript ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcription status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transcription status"
        )

@router.get("/")
async def list_transcripts(
    auth: AuthContext = Depends(get_auth_context),
    limit: int = 20,
    offset: int = 0,
    status_filter: str = None
):
    """List user's transcripts with pagination and optional status filtering"""
    try:
        # Validate pagination parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset must be non-negative"
            )
        
        # Validate status filter if provided
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if status_filter and status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get user's client for authorization
        client = await supabase_service.get_user_client(auth.user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # For now, get all user transcripts (we'll add pagination to service layer later)
        user_transcripts = await supabase_service.get_user_transcripts(auth.user.id, auth.access_token)
        
        # Filter by client (extra security layer)
        client_transcripts = [t for t in user_transcripts if t.client_id == client.id]
        
        # Apply status filter if provided
        if status_filter:
            client_transcripts = [t for t in client_transcripts if t.status == status_filter]
        
        # Apply pagination
        total_count = len(client_transcripts)
        paginated_transcripts = client_transcripts[offset:offset + limit]
        
        # Format response
        transcripts_data = []
        for transcript in paginated_transcripts:
            transcripts_data.append({
                "transcript_id": str(transcript.id),
                "video_id": str(transcript.video_id),
                "status": transcript.status,
                "created_at": transcript.created_at.isoformat(),
                "updated_at": transcript.updated_at.isoformat(),
                "request_id": transcript.request_id,
                "error_message": transcript.error_message,
                "has_content": bool(transcript.raw_transcript or transcript.processed_transcript)
            })
        
        return {
            "transcripts": transcripts_data,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "filters": {
                "status": status_filter
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing transcripts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list transcripts"
        )

@router.get("/video/{video_id}")
async def get_video_transcript(
    video_id: str,
    auth: AuthContext = Depends(get_auth_context)
):
    """Get transcript for a specific video"""
    try:
        from uuid import UUID
        video_uuid = UUID(video_id)
        
        # Get user's client for authorization
        client = await supabase_service.get_user_client(auth.user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # Get transcript for the video
        transcript = await supabase_service.get_video_transcript(video_uuid, auth.access_token)
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found for this video"
            )
        
        # Check authorization - user can only access their client's transcripts
        if transcript.client_id != client.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: transcript belongs to different organization"
            )
        
        # Format basic transcript info (similar to status endpoint)
        return {
            "transcript_id": str(transcript.id),
            "video_id": str(transcript.video_id),
            "status": transcript.status,
            "created_at": transcript.created_at.isoformat(),
            "updated_at": transcript.updated_at.isoformat(),
            "request_id": transcript.request_id,
            "error_message": transcript.error_message,
            "has_content": bool(transcript.raw_transcript or transcript.processed_transcript)
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving video transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video transcript"
        )

@router.get("/{transcript_id}")
async def get_transcript(
    transcript_id: str,
    auth: AuthContext = Depends(get_auth_context)
):
    """Get full transcript content with video information"""
    try:
        from uuid import UUID
        transcript_uuid = UUID(transcript_id)
        
        # Get user's client for authorization
        client = await supabase_service.get_user_client(auth.user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # Get transcript with media information using JOIN
        transcript_data = await supabase_service.get_transcript_with_media(transcript_uuid, auth.access_token)
        if not transcript_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )
        
        # Check authorization - user can only access their client's transcripts
        if transcript_data.get("client_id") != str(client.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: transcript belongs to different organization"
            )
        
        # Extract media information
        video_info = transcript_data.get("media", {})
        
        # Format transcript content
        content = None
        if transcript_data.get("status") == "completed" and transcript_data.get("raw_transcript"):
            raw_transcript = transcript_data.get("raw_transcript", {})
            processed_transcript = transcript_data.get("processed_transcript", {})
            
            # Extract content from Deepgram response format
            content = {
                "full_transcript": "",
                "utterances": [],
                "confidence": 0.0
            }
            
            # Parse Deepgram results format
            if "results" in raw_transcript and "channels" in raw_transcript["results"]:
                channels = raw_transcript["results"]["channels"]
                if channels and len(channels) > 0:
                    alternatives = channels[0].get("alternatives", [])
                    if alternatives and len(alternatives) > 0:
                        alt = alternatives[0]
                        content["full_transcript"] = alt.get("transcript", "")
                        content["confidence"] = alt.get("confidence", 0.0)
                        
                        # Extract utterances with speaker info
                        utterances = alt.get("utterances", [])
                        content["utterances"] = [
                            {
                                "speaker": utt.get("speaker", 0),
                                "text": utt.get("transcript", ""),
                                "start": utt.get("start", 0.0),
                                "end": utt.get("end", 0.0),
                                "confidence": utt.get("confidence", 0.0)
                            }
                            for utt in utterances
                        ]
        
        # Calculate duration from video metadata if available
        duration_seconds = None
        if video_info and "metadata" in video_info:
            metadata = video_info.get("metadata", {})
            duration_seconds = metadata.get("duration_seconds")
        
        return {
            "transcript_id": transcript_data.get("id"),
            "video": {
                "id": video_info.get("id"),
                "filename": video_info.get("filename"),
                "duration_seconds": duration_seconds,
                "size_bytes": video_info.get("size_bytes"),
                "content_type": video_info.get("content_type")
            },
            "status": transcript_data.get("status"),
            "content": content,
            "created_at": transcript_data.get("created_at"),
            "updated_at": transcript_data.get("updated_at"),
            "completed_at": transcript_data.get("updated_at") if transcript_data.get("status") == "completed" else None,
            "request_id": transcript_data.get("request_id"),
            "error_message": transcript_data.get("error_message")
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transcript ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcript"
        )

@router.get("/callback/test")
async def test_callback():
    """Test endpoint to verify callback URL is accessible"""
    return {
        "status": "ok",
        "message": "Callback endpoint is accessible",
        "timestamp": datetime.now(UTC).isoformat()
    }

@router.post("/webhooks/upload-complete")
async def handle_upload_complete(request: Request):
    """
    Webhook endpoint for Supabase Storage upload completion
    Triggers smart routing and background processing
    """
    try:
        logger.info("🔔 Upload completion webhook received")
        
        # Verify webhook authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.error("❌ Missing or invalid Authorization header")
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        
        token = auth_header.split(" ")[1]
        if token != settings.WEBHOOK_SECRET_TOKEN:
            logger.error("❌ Invalid webhook token")
            raise HTTPException(status_code=401, detail="Invalid webhook token")
        
        logger.info("✅ Webhook authentication verified")
        
        # Parse webhook payload
        body = await request.body()
        webhook_data = json.loads(body.decode('utf-8'))
        
        logger.info(f"Webhook data: {json.dumps(webhook_data, indent=2)[:500]}...")
        
        # Handle both Edge Function and Dashboard Webhook formats
        if webhook_data.get("type") == "UPDATE" and webhook_data.get("table") == "media":
            # Dashboard Webhook format
            logger.info("📋 Processing Dashboard Webhook format")
            
            record = webhook_data.get("record", {})
            old_record = webhook_data.get("old_record", {})
            
            # Check if upload_status changed to 'completed'
            if record.get("upload_status") != "completed":
                logger.info(f"ℹ️ Upload status is '{record.get('upload_status')}', not 'completed' - ignoring")
                return {"message": "Upload status not completed - ignored"}
            
            if old_record.get("upload_status") == "completed":
                logger.info("ℹ️ Upload was already completed - ignoring duplicate")
                return {"message": "Upload already completed - ignored"}
                
            # Extract media details from record
            media_id = str(record.get("id"))
            user_id = str(record.get("created_by"))
            client_id = str(record.get("client_id"))
            filename = record.get("filename")
            media_metadata = record.get("metadata", {})
            
            file_category = media_metadata.get("file_category", "unknown")
            processing_type = media_metadata.get("processing_type", "unknown")
            
            logger.info(f"📋 Processing upload completion for {file_category} file")
            logger.info(f"   Media ID: {media_id}")
            logger.info(f"   Client ID: {client_id}")
            logger.info(f"   User ID: {user_id}")
            logger.info(f"   Processing type: {processing_type}")
            
        else:
            # Edge Function format (for manual testing)
            logger.info("📋 Processing Edge Function format")
            
            object_name = webhook_data.get("object_name") or webhook_data.get("name")
            bucket_name = webhook_data.get("bucket_name") or webhook_data.get("bucket")
            metadata = webhook_data.get("metadata", {})
            
            if not object_name:
                logger.error("❌ No object_name found in webhook data")
                raise HTTPException(status_code=400, detail="Missing object_name in webhook")
            
            # Parse client_id from storage path: clients/{client_id}/uploads/filename.mp3
            path_parts = object_name.split("/")
            if len(path_parts) < 3:
                logger.error(f"❌ Invalid storage path format: {object_name}")
                raise HTTPException(status_code=400, detail="Invalid storage path format")
            
            client_id = path_parts[1]  # Extract client_id from path
            filename = path_parts[-1]  # Extract filename
            
            # Find media record by filename and client_id
            try:
                media_records = await supabase_service.get_media_by_filename_and_client(
                    filename=filename,
                    client_id=client_id,
                    access_token=settings.SUPABASE_SERVICE_ROLE_KEY
                )
                
                if not media_records:
                    logger.error(f"❌ No media record found for {filename} in client {client_id}")
                    raise HTTPException(status_code=404, detail="Media record not found")
                
                # Get the most recent media record (in case of duplicates)
                media = media_records[0]
                media_metadata = media.metadata or {}
                
                media_id = str(media.id)
                user_id = str(media.created_by)
                file_category = media_metadata.get("file_category", "unknown")
                needs_audio_extraction = media_metadata.get("needs_audio_extraction", False)
                processing_type = media_metadata.get("processing_type", "unknown")
                
                logger.info(f"📋 Processing upload completion for {file_category} file")
                logger.info(f"   Media ID: {media_id}")
                logger.info(f"   Client ID: {client_id}")
                logger.info(f"   User ID: {user_id}")
                logger.info(f"   Processing type: {processing_type}")
                
            except Exception as e:
                logger.error(f"❌ Failed to get media record: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to get media record: {str(e)}")
        
        # For Dashboard Webhook format, status is already completed
        # For Edge Function format, update media status to completed
        if webhook_data.get("type") != "UPDATE":
            await supabase_service.update_media(
                media_id,
                {
                    "metadata": {
                        **media_metadata,
                        "webhook_received_at": datetime.now(UTC).isoformat()
                    }
                },
                user_id
            )
            logger.info(f"✅ Updated media {media_id} with webhook timestamp")
        else:
            logger.info(f"✅ Media {media_id} already completed via Dashboard Webhook")
        
        # Construct storage_path for background processing
        if webhook_data.get("type") == "UPDATE":
            # Dashboard Webhook format - construct path from database record
            storage_path = f"clients/{client_id}/uploads/{filename}"
        else:
            # Edge Function format - use object_name
            storage_path = object_name
        
        # Start background processing based on file type (SMART ROUTING)
        transcript_id = None
        if file_category == "audio":
            logger.info(f"🎵 Starting audio processing pipeline")
            transcript_id = await start_audio_transcription_background(
                media_id=media_id,
                storage_path=storage_path,
                client_id=client_id,
                user_id=user_id
            )
        elif file_category == "video":
            logger.info(f"🎬 Starting video processing pipeline (audio extraction)")
            transcript_id = await start_video_processing_background(
                media_id=media_id,
                storage_path=storage_path,
                client_id=client_id,
                user_id=user_id
            )
        else:
            logger.warning(f"⚠️ Unknown file category: {file_category}")
            raise HTTPException(status_code=400, detail=f"Unsupported file category: {file_category}")
        
        return {
            "status": "success",
            "message": "Upload processed and transcription started",
            "media_id": media_id,
            "transcript_id": str(transcript_id) if transcript_id else None,
            "processing_type": processing_type,
            "processed_at": datetime.now(UTC).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Upload webhook processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload webhook processing failed: {str(e)}"
        )

async def start_audio_transcription_background(media_id: str, storage_path: str, client_id: str, user_id: str) -> str:
    """Background audio processing - direct transcription, returns transcript_id"""
    try:
        logger.info(f"🎵 Starting audio transcription for media {media_id}")
        
        # Create transcript record with proper user context
        # Use system method to preserve user_id for audit fields
        transcript = await supabase_service.create_transcript_system(
            TranscriptCreate(
                video_id=media_id,  # Using media_id for consistency
                client_id=client_id,
                status="processing",
                metadata={
                    "audio_storage_path": storage_path,
                    "processing_type": "direct_audio"
                }
            ),
            user_id  # Pass user_id to maintain audit context
        )
        logger.info(f"✅ Created transcript record: {transcript.id}")
        
        # Store transcript_id to return
        transcript_id = transcript.id
        
        # Get signed URL for Deepgram
        audio_signed_url = await supabase_service.get_signed_url(
            bucket=settings.STORAGE_BUCKET,
            path=storage_path,
            expires_in=3600
        )
        
        # Start Deepgram transcription
        result = await deepgram_service.transcribe_from_url(audio_signed_url)
        logger.info(f"✅ Deepgram transcription started: {result.get('request_id')}")
        
        # Update transcript with request_id
        await supabase_service.update_transcript_system(
            transcript.id,
            {"request_id": result.get("request_id")},
            user_id
        )
        
        # Return transcript_id for webhook response
        return str(transcript_id)
        
    except Exception as e:
        logger.error(f"❌ Audio transcription background processing failed: {str(e)}", exc_info=True)
        # Update transcript status to failed if it was created
        if 'transcript_id' in locals():
            await supabase_service.update_transcript_system(
                transcript_id,
                {"status": "failed", "error_message": str(e)},
                user_id
            )
        raise

async def start_video_processing_background(media_id: str, storage_path: str, client_id: str, user_id: str) -> str:
    """Background video processing with audio extraction, returns transcript_id"""
    try:
        logger.info(f"🎬 Starting video processing for media {media_id}")
        
        # Extract audio from video using existing audio extraction service
        # The service will handle downloading video, extracting audio, and uploading audio
        audio_storage_path, _ = await audio_extraction_service.extract_and_upload_audio_from_storage(
            video_storage_path=storage_path,
            client_id=client_id,
            media_id=media_id
        )
        logger.info(f"✅ Audio extracted to: {audio_storage_path}")
        
        # Create transcript record with proper user context
        # Use system method to preserve user_id for audit fields
        transcript = await supabase_service.create_transcript_system(
            TranscriptCreate(
                video_id=media_id,  # Using media_id for consistency
                client_id=client_id,
                status="processing",
                metadata={
                    "audio_storage_path": audio_storage_path,
                    "video_storage_path": storage_path,
                    "processing_type": "video_extraction"
                }
            ),
            user_id  # Pass user_id to maintain audit context
        )
        logger.info(f"✅ Created transcript record: {transcript.id}")
        
        # Store transcript_id to return
        transcript_id = transcript.id
        
        # Get signed URL for extracted audio
        audio_signed_url = await supabase_service.get_signed_url(
            bucket=settings.STORAGE_BUCKET,
            path=audio_storage_path,
            expires_in=3600
        )
        
        # Start Deepgram transcription
        result = await deepgram_service.transcribe_from_url(audio_signed_url)
        logger.info(f"✅ Deepgram transcription started: {result.get('request_id')}")
        
        # Update transcript with request_id
        await supabase_service.update_transcript_system(
            transcript.id,
            {"request_id": result.get("request_id")},
            user_id
        )
        
        # Return transcript_id for webhook response
        return str(transcript_id)
        
    except Exception as e:
        logger.error(f"❌ Video processing background processing failed: {str(e)}", exc_info=True)
        # Update transcript status to failed if it was created
        if 'transcript_id' in locals():
            await supabase_service.update_transcript_system(
                transcript_id,
                {"status": "failed", "error_message": str(e)},
                user_id
            )
        raise

@router.post("/callback")
async def transcription_callback(request: Request):
    """
    Callback endpoint for Deepgram transcription results
    Enhanced with robust error handling and debugging
    """
    # Log incoming request details for debugging
    logger.info(f"🔔 Deepgram callback received")
    logger.info(f"   Method: {request.method}")
    logger.info(f"   URL: {request.url}")
    logger.info(f"   Headers: {dict(request.headers)}")
    
    try:
        # Get raw body first for debugging
        body = await request.body()
        logger.info(f"   Body size: {len(body)} bytes")
        logger.info(f"   Content-Type: {request.headers.get('content-type', 'Not set')}")
        
        # Handle different content types
        content_type = request.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            # Parse as JSON
            try:
                # Reset request state and parse JSON
                data = await request.json()
                logger.info("✅ Successfully parsed JSON payload")
            except Exception as json_error:
                logger.error(f"❌ JSON parsing failed: {json_error}")
                logger.info(f"Raw body: {body.decode('utf-8', errors='ignore')[:1000]}...")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON payload: {str(json_error)}"
                )
        else:
            # Try to parse as JSON anyway (some services don't set correct content-type)
            try:
                data = json.loads(body.decode('utf-8'))
                logger.info("✅ Successfully parsed JSON from body (despite content-type)")
            except Exception as parse_error:
                logger.error(f"❌ Could not parse as JSON: {parse_error}")
                logger.info(f"Raw body: {body.decode('utf-8', errors='ignore')[:1000]}...")
                # Return success for non-JSON webhooks (some services send test pings)
                return {
                    "status": "received",
                    "message": "Non-JSON callback received",
                    "content_type": content_type
                }
        
        # Extract request_id for correlation
        request_id = data.get('metadata', {}).get('request_id') or data.get('request_id')
        logger.info(f"📋 Request ID: {request_id}")
        
        # Extract and log the transcript details
        if 'results' in data and 'channels' in data['results']:
            logger.info("🎯 Processing transcription results...")
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
            logger.warning("⚠️ No transcript data found in callback payload")
            
        # Log the complete raw data for debugging (truncated for large payloads)
        data_str = json.dumps(data, indent=2)
        if len(data_str) > 10000:
            logger.info(f"\n📄 Complete callback data (truncated - {len(data_str)} chars total):")
            logger.info(data_str[:10000] + "\n... [TRUNCATED]")
        else:
            logger.info("\n📄 Complete callback data:")
            logger.info(data_str)
        
        # **NEW: Store transcription results in database**
        if request_id:
            try:
                logger.info(f"💾 Updating transcript record for request_id: {request_id}")
                
                # Find transcript by request_id
                transcript = await supabase_service.get_transcript_by_request_id(request_id)
                if transcript:
                    logger.info(f"✅ Found transcript record: {transcript.id}")
                    
                    # Determine status based on transcript content
                    new_status = "completed"
                    error_message = None
                    
                    # Check if transcription was successful
                    if 'results' in data and 'channels' in data['results']:
                        channels = data['results']['channels']
                        if channels and len(channels) > 0 and 'alternatives' in channels[0]:
                            alternatives = channels[0]['alternatives']
                            if alternatives and len(alternatives) > 0:
                                transcript_text = alternatives[0].get('transcript', '').strip()
                                if not transcript_text:
                                    new_status = "failed"
                                    error_message = "No transcript content received from Deepgram"
                            else:
                                new_status = "failed"
                                error_message = "No alternatives found in Deepgram response"
                        else:
                            new_status = "failed"
                            error_message = "No channels found in Deepgram response"
                    else:
                        new_status = "failed"
                        error_message = "Invalid Deepgram response structure"
                    
                    # Update transcript with results
                    update_data = {
                        "status": new_status,
                        "raw_transcript": data,
                        "processed_transcript": {"processed_at": datetime.now(UTC).isoformat()},
                        "error_message": error_message
                    }
                    
                    updated_transcript = await supabase_service.update_transcript_system(transcript.id, update_data, transcript.created_by)
                    if updated_transcript:
                        logger.info(f"✅ Transcript updated successfully - Status: {new_status}")
                        
                        # Schedule audio file cleanup after retention period
                        if new_status == "completed":
                            try:
                                # Get audio storage path from transcript metadata
                                metadata = transcript.metadata or {}
                                audio_storage_path = metadata.get("audio_storage_path")
                                
                                if audio_storage_path:
                                    if settings.AUDIO_RETENTION_DAYS > 0:
                                        # Schedule cleanup after retention period
                                        logger.info(f"📅 Audio file scheduled for cleanup after {settings.AUDIO_RETENTION_DAYS} days: {audio_storage_path}")
                                        
                                        # Update transcript metadata with cleanup schedule
                                        cleanup_date = datetime.now(UTC) + timedelta(days=settings.AUDIO_RETENTION_DAYS)
                                        updated_metadata = metadata.copy()
                                        updated_metadata["audio_cleanup_scheduled"] = cleanup_date.isoformat()
                                        
                                        await supabase_service.update_transcript_system(
                                            transcript.id, 
                                            {"metadata": updated_metadata}, 
                                            transcript.created_by
                                        )
                                    else:
                                        # Immediate cleanup (legacy behavior)
                                        await audio_extraction_service.cleanup_audio_file(audio_storage_path)
                                        logger.info(f"🧹 Immediate cleanup: {audio_storage_path}")
                                else:
                                    logger.info(f"ℹ️ No audio storage path found in transcript metadata")
                                    
                            except Exception as cleanup_error:
                                logger.warning(f"⚠️ Failed to schedule audio cleanup: {str(cleanup_error)}")
                                # Don't fail the callback for cleanup errors
                        
                    else:
                        logger.error("❌ Failed to update transcript record")
                else:
                    logger.warning(f"⚠️ No transcript found with request_id: {request_id}")
                    
            except Exception as db_error:
                logger.error(f"💥 Error updating transcript in database: {str(db_error)}", exc_info=True)
                # Don't fail the callback - Deepgram expects 200 response
        else:
            logger.warning("⚠️ No request_id found in callback data - cannot update transcript")
        
        return {
            "status": "success",
            "message": "Callback received and processed",
            "processed_at": datetime.now(UTC).isoformat(),
            "request_id": request_id
        }
            
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 Bad Request)
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected error processing Deepgram callback: {str(e)}", exc_info=True)
        # Return 500 for unexpected errors, but log details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process callback: {str(e)}"
        )

@router.post("/admin/cleanup-audio")
async def cleanup_expired_audio_files(current_user: User = Depends(get_current_user)):
    """
    Admin endpoint to manually trigger cleanup of expired audio files
    Only accessible by admin users
    """
    try:
        # Check if user is admin (you can modify this check based on your admin logic)
        if current_user.email != settings.ADMIN_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        logger.info(f"🔧 Admin audio cleanup triggered by: {current_user.email}")
        
        # Run the cleanup
        result = await audio_cleanup_service.cleanup_expired_audio_files()
        
        return {
            "success": True,
            "message": "Audio cleanup completed",
            "details": result,
            "triggered_by": current_user.email,
            "triggered_at": datetime.now(UTC).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in admin audio cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )

@router.get("/admin/cleanup-stats")
async def get_audio_cleanup_statistics(current_user: User = Depends(get_current_user)):
    """
    Admin endpoint to get statistics about audio file cleanup
    Only accessible by admin users
    """
    try:
        # Check if user is admin
        if current_user.email != settings.ADMIN_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Get cleanup statistics
        stats = await audio_cleanup_service.get_cleanup_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "retrieved_by": current_user.email,
            "retrieved_at": datetime.now(UTC).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting cleanup statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

