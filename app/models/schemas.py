from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import uuid

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SegmentType(str, Enum):
    """Types of segments in a church service"""
    sermon = "sermon"
    prayer = "prayer"
    worship = "worship"
    admin = "admin"
    other = "other"

class ContentType(str, Enum):
    """Types of content that can be generated"""
    devotional = "devotional"
    summary = "summary"
    discussion = "discussion"
    whats_on = "whats_on"

class Segment(BaseModel):
    """A segment of a church service"""
    type: SegmentType
    text: str
    start_time: float
    end_time: float
    confidence: float

class GeneratedContent(BaseModel):
    """Content generated from sermon segments"""
    type: ContentType
    content: str
    metadata: Dict[str, Any] = {}

class TranscriptionRequest(BaseModel):
    """Request to transcribe a video"""
    video_url: str
    mime_type: str

class TranscriptionResponse(BaseModel):
    """Response from transcription service"""
    segments: list[Segment]
    metadata: Dict[str, Any] = {}

class ContentGenerationRequest(BaseModel):
    """Request to generate content"""
    segments: list[Segment]
    content_type: ContentType

class ContentGenerationResponse(BaseModel):
    """Response from content generation"""
    content: GeneratedContent
    metadata: Dict[str, Any] = {}

class ContentGenerationError(BaseModel):
    """Error details for content generation failures"""
    error_type: str
    error_message: str
    content_type: ContentType
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SegmentedTranscriptionResponse(TranscriptionResponse):
    """Response with segmented transcription"""
    segments: List[Segment]
    sermon_segments: List[Segment]
    admin_segments: List[Segment]

class AsyncTranscriptionResponse(TranscriptionResponse):
    """Response for async transcription requests"""
    request_id: str
    callback_url: str

class CallbackResponse(BaseModel):
    """Response for Deepgram callbacks"""
    status: str
    message: str
    request_id: str
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat()) 