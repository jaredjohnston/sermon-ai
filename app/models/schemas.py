from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, EmailStr
import uuid
from uuid import UUID

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
    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class UserBase(BaseModel):
    """Base user model"""
    email: str

class UserCreate(UserBase):
    """User creation model with extended fields"""
    password: str
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    country: str = Field(..., min_length=2, max_length=100)
    organization_name: str = Field(..., min_length=2, max_length=100)  # This becomes the client name

class User(UserBase):
    """User model with ID"""
    id: UUID
    created_at: datetime

class UserProfileBase(BaseModel):
    """Base user profile model"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    country: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    """User profile creation model"""
    pass

class UserProfile(UserProfileBase):
    """User profile model with ID and timestamps"""
    id: UUID
    user_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

class UserWithProfile(User):
    """User model with profile information"""
    profile: Optional[UserProfile] = None

class TeamBase(BaseModel):
    """Base team model"""
    name: str

class TeamCreate(TeamBase):
    """Team creation model"""
    pass

class Team(TeamBase):
    """Team model with ID and timestamps"""
    id: UUID
    created_at: datetime
    updated_at: datetime

class TeamMemberBase(BaseModel):
    """Base team member model"""
    team_id: UUID
    role: str = "member"

class TeamMemberCreate(TeamMemberBase):
    """Team member creation model"""
    pass

class TeamMember(TeamMemberBase):
    """Team member model with user ID"""
    user_id: UUID
    created_at: datetime

class MediaBase(BaseModel):
    """Base media model - supports video, audio, and documents"""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., pattern=r'^(video|audio|text|application)/[\w\.-]+$')
    size_bytes: int = Field(..., gt=0)
    client_id: UUID
    storage_path: str = Field(..., min_length=1, max_length=512)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MediaCreate(MediaBase):
    """Media creation model"""
    pass

class Media(MediaBase):
    """Media model with ID and timestamps"""
    id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

# Backward compatibility aliases
VideoBase = MediaBase
VideoCreate = MediaCreate  
Video = Media

class SubscriptionStatus(str, Enum):
    """Client subscription status"""
    active = "active"
    inactive = "inactive"
    trial = "trial"

class TranscriptStatus(str, Enum):
    """Status of a transcript"""
    processing = "processing"
    completed = "completed"
    failed = "failed"
    pending = "pending"

class TranscriptBase(BaseModel):
    """Base transcript model"""
    video_id: UUID
    client_id: UUID
    status: TranscriptStatus = Field(default=TranscriptStatus.processing)
    raw_transcript: Optional[Dict[str, Any]] = None
    processed_transcript: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TranscriptCreate(TranscriptBase):
    """Request to create a transcript"""
    pass

class Transcript(TranscriptBase):
    """Transcript model with ID and timestamps"""
    id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

# Response models
class TeamResponse(Team):
    """Team response model with members"""
    members: List[TeamMember] = []

class VideoResponse(Video):
    """Video response model with transcript"""
    transcript: Optional[Transcript] = None

class UserRole(str, Enum):
    """User roles in a client"""
    owner = "owner"
    member = "member"

class ClientBase(BaseModel):
    """Base client model"""
    name: str = Field(..., min_length=2, max_length=100)
    subscription_status: SubscriptionStatus = Field(default=SubscriptionStatus.trial)

class ClientCreate(ClientBase):
    """Client creation model"""
    pass

class Client(ClientBase):
    """Client model with ID and timestamps"""
    id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

class ClientUserBase(BaseModel):
    """Base client user model"""
    client_id: UUID
    user_id: UUID
    role: UserRole = Field(default=UserRole.member)

class ClientUserCreate(ClientUserBase):
    """Client user creation model"""
    email: EmailStr  # Used for invitation but not stored in DB

class ClientUser(ClientUserBase):
    """Client user model with timestamps"""
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

class ClientResponse(Client):
    """Client response with users"""
    users: List[ClientUser] = []

class SignUpResponse(BaseModel):
    """Enhanced signup response with user, profile, and client"""
    user: User
    profile: UserProfile
    client: Client
    role: UserRole = UserRole.owner
    access_token: str

# Content Template Models
class TemplateStatus(str, Enum):
    """Status of content templates"""
    draft = "draft"
    active = "active"
    archived = "archived"

class ContentTemplateBase(BaseModel):
    """Base content template model"""
    model_config = {"protected_namespaces": ()}
    
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content_type_name: str = Field(..., min_length=2, max_length=50)
    structured_prompt: str = Field(..., min_length=50, max_length=5000)
    example_content: List[str] = Field(default_factory=list)
    status: TemplateStatus = Field(default=TemplateStatus.active)
    model_settings: Dict[str, Any] = Field(default_factory=lambda: {
        "temperature": 0.7,
        "max_tokens": 2000,
        "model": "gpt-4o"
    })

class ContentTemplateCreate(ContentTemplateBase):
    """Content template creation model"""
    client_id: UUID

class ContentTemplate(ContentTemplateBase):
    """Content template model with ID and timestamps"""
    id: UUID
    client_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

class ContentTemplateUpdate(BaseModel):
    """Content template update model"""
    model_config = {"protected_namespaces": ()}
    
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    structured_prompt: Optional[str] = Field(None, min_length=50, max_length=5000)
    example_content: Optional[List[str]] = None
    status: Optional[TemplateStatus] = None
    model_settings: Optional[Dict[str, Any]] = None

class ContentTemplatePublic(BaseModel):
    """Public template model (only shows what users should see)"""
    model_config = {"protected_namespaces": ()}
    
    id: UUID
    name: str
    description: Optional[str] = None
    content_type_name: str
    example_content: List[str] = Field(default_factory=list)

# Generated Content Models
class GeneratedContentBase(BaseModel):
    """Base generated content model"""
    transcript_id: UUID
    template_id: UUID
    content: str
    content_metadata: Dict[str, Any] = Field(default_factory=dict)
    generation_settings: Dict[str, Any] = Field(default_factory=dict)
    generation_cost_cents: Optional[int] = None
    generation_duration_ms: Optional[int] = None
    user_edits_count: int = Field(default=0)
    last_edited_at: Optional[datetime] = None

class GeneratedContentCreate(GeneratedContentBase):
    """Generated content creation model"""
    client_id: UUID

class GeneratedContentModel(GeneratedContentBase):
    """Generated content model with ID and timestamps"""
    id: UUID
    client_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

class GeneratedContentUpdate(BaseModel):
    """Generated content update model"""
    content: Optional[str] = None
    user_edits_count: Optional[int] = None
    last_edited_at: Optional[datetime] = None

# Content Generation Request/Response Models
class ContentGenerationRequest(BaseModel):
    """Request to generate content from transcript"""
    transcript_id: UUID
    template_id: UUID
    custom_instructions: Optional[str] = Field(None, max_length=1000)

class ContentGenerationResponse(BaseModel):
    """Response from content generation"""
    id: UUID
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generation_cost_cents: Optional[int] = None
    generation_duration_ms: Optional[int] = None

# Template Pattern Extraction Models
class TemplateExtractionRequest(BaseModel):
    """Request to extract patterns from examples"""
    content_type_name: str = Field(..., min_length=2, max_length=100, description="User-defined content type (e.g., 'small group guide', 'Facebook post')")
    examples: List[str] = Field(..., min_items=1, max_items=5, description="2-5 examples of the content type you want to create")
    description: Optional[str] = Field(None, max_length=500, description="Optional description to provide more context about this content type")

class TemplateExtractionResponse(BaseModel):
    """Response from template pattern extraction"""
    structured_prompt: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    extracted_patterns: Dict[str, Any] = Field(default_factory=dict)

# Upload Preparation Models
class PrepareUploadRequest(BaseModel):
    """Request to prepare a file upload"""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., pattern=r'^(video|audio|text|application)/[\w\.-]+$')
    size_bytes: int = Field(..., gt=0, le=50 * 1024 * 1024 * 1024)  # 50GB max

class TUSConfig(BaseModel):
    """TUS resumable upload configuration"""
    upload_url: str = Field(..., description="TUS upload endpoint URL")
    headers: Dict[str, str] = Field(..., description="Required headers for TUS upload")
    metadata: Dict[str, str] = Field(..., description="TUS metadata for the upload")
    chunk_size: int = Field(default=6 * 1024 * 1024, description="Recommended chunk size in bytes")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_delay: int = Field(default=1000, description="Delay between retries in milliseconds")
    timeout: int = Field(default=30000, description="Request timeout in milliseconds")
    parallel_uploads: int = Field(default=1, description="Number of parallel chunk uploads")
    store_url: Optional[str] = Field(None, description="URL to store upload progress/state")

class PrepareUploadResponse(BaseModel):
    """Response from upload preparation"""
    upload_url: str
    upload_fields: Dict[str, Any]
    media_id: str
    processing_info: Dict[str, Any]
    upload_method: str = Field(description="Upload method: 'http_put' or 'tus_resumable'")
    tus_config: Optional[TUSConfig] = Field(None, description="TUS configuration for resumable uploads")
    expires_in: int = Field(default=3600)  # 1 hour

class UploadStatusResponse(BaseModel):
    """Response for upload status check"""
    media_id: str
    upload_status: str  # preparing, uploading, completed, failed
    processing_stage: str  # upload_complete, extracting_audio, transcribing, completed, failed
    file_category: str  # audio, video
    transcript_id: Optional[str] = None
    transcript_status: Optional[str] = None
    error_message: Optional[str] = None 