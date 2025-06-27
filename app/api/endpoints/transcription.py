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
from app.middleware.auth import get_current_user
from app.models.schemas import User, MediaCreate, VideoCreate, TranscriptCreate
from datetime import datetime, UTC, timedelta
import json

logger = logging.getLogger(__name__)
router = APIRouter()


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
                current_user.id
            )
            logger.info(f"Media record created: {video.id}")  # Keep 'video' var for backward compatibility
            
            # STEP 3: Sequential stream save, then concurrent processing
            logger.info(f"Starting concurrent video upload and audio extraction for {file_size_mb}MB file...")
            
            # STEP 4: Extract audio and get temp file for video upload
            logger.info(f"Extracting audio for immediate transcription...")
            try:
                audio_storage_path, audio_signed_url, temp_video_path = await extract_and_upload_audio(
                    file, client.id, str(video.id)
                )
                logger.info(f"Audio extracted and uploaded - starting transcription immediately")
                
                # STEP 5: Create transcript tracking record BEFORE starting transcription
                # This prevents race condition where callback fires before record exists
                transcript = await supabase_service.create_transcript(
                    TranscriptCreate(
                        video_id=video.id,
                        client_id=client.id,
                        status="processing",
                        request_id=None,  # Will be updated after Deepgram call
                        metadata={"audio_storage_path": audio_storage_path}  # Store for cleanup
                    ),
                    current_user.id
                )
                logger.info(f"Transcript record created: {transcript.id}")
                
                # Start transcription with audio immediately (don't wait for video upload)
                result = await deepgram_service.transcribe_from_url(audio_signed_url)
                logger.info(f"Transcription started with request_id: {result.get('request_id')}")
                
                # Update transcript record with request_id from Deepgram
                transcript = await supabase_service.update_transcript(
                    transcript.id,
                    {"request_id": result.get("request_id")},
                    current_user.id
                )
                logger.info(f"Transcript updated with request_id: {result.get('request_id')}")
                
                # Start video upload in background using the temp file
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
            except Exception as e:
                logger.error(f"Audio processing failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Audio processing failed: {str(e)}"
                )
            
            # Video upload continues in background - we don't wait for it
            logger.info(f"Video upload continues in background while transcription processes...")
            
            # SUCCESS: Return comprehensive status information
            return {
                "success": True,
                "message": "Audio extracted and transcription started immediately. Video upload continues in background.",
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
                    "audio_extracted": True,
                    "transcription_started": True,
                    "video_upload_status": "background_processing"
                },
                "next_steps": {
                    "description": "Transcription processing from extracted audio (faster than full video)",
                    "estimated_time": f"~{max(2, int(file_size_mb / 100))} minutes",  # Faster estimate for audio
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
    """List all media (videos, audio, documents) for the current user's client"""
    try:
        # Get user's client
        client = await supabase_service.get_user_client(current_user.id)
        if not client:
            return []
            
        videos = await supabase_service.get_client_media(client.id)
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
    current_user: User = Depends(get_current_user)
):
    """Get the current status of a transcription job"""
    try:
        from uuid import UUID
        transcript_uuid = UUID(transcript_id)
        
        # Get user's client for authorization
        client = await supabase_service.get_user_client(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # Get transcript
        transcript = await supabase_service.get_transcript(transcript_uuid)
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
    current_user: User = Depends(get_current_user),
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
        client = await supabase_service.get_user_client(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # For now, get all user transcripts (we'll add pagination to service layer later)
        user_transcripts = await supabase_service.get_user_transcripts(current_user.id)
        
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
    current_user: User = Depends(get_current_user)
):
    """Get transcript for a specific video"""
    try:
        from uuid import UUID
        video_uuid = UUID(video_id)
        
        # Get user's client for authorization
        client = await supabase_service.get_user_client(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # Get transcript for the video
        transcript = await supabase_service.get_video_transcript(video_uuid)
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
    current_user: User = Depends(get_current_user)
):
    """Get full transcript content with video information"""
    try:
        from uuid import UUID
        transcript_uuid = UUID(transcript_id)
        
        # Get user's client for authorization
        client = await supabase_service.get_user_client(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to access transcripts"
            )
        
        # Get transcript with media information using JOIN
        transcript_data = await supabase_service.get_transcript_with_media(transcript_uuid)
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
                    
                    updated_transcript = await supabase_service.update_transcript(transcript.id, update_data, transcript.created_by)
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
                                        
                                        await supabase_service.update_transcript(
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
