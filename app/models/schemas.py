from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SegmentType(str, Enum):
    """Types of segments in a church service"""
    WORSHIP = "worship"
    WELCOME = "welcome"
    SERMON = "sermon"
    ADMIN = "admin"
    TITHING = "tithing"
    OTHER = "other"

class Segment(BaseModel):
    """A segment of transcribed content"""
    type: SegmentType
    text: str
    start_time: float
    end_time: float
    confidence: float

class TranscriptionResponse(BaseModel):
    """Base transcription response"""
    message: str
    filename: str
    size: str
    content_type: str
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

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