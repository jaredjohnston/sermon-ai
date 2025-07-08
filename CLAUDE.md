# TUS Upload & Transcription System Architecture

## 🎯 High-Level System Overview

```
Frontend → Backend → Supabase Storage → Webhook → Background Processing → Deepgram → Database
   ↓         ↓           ↓                ↓              ↓                    ↓         ↓
Validate   Create     TUS Upload      Detect File    Smart Routing      Transcription  Results
           Media                      Category       Audio/Video        via Signed URL
```

## 📋 Complete Flow Breakdown

### Phase 1: Upload Preparation & Validation
```pseudocode
1. Frontend selects file (e.g., 86MB audio file)
2. Frontend calls POST /api/v1/transcription/upload/prepare
3. Backend validates:
   - File size (< 50GB)
   - Content type (audio/* or video/*)
   - User authentication & client relationship
4. Backend determines:
   - file_category = "audio" | "video"
   - processing_requirements = smart routing config
   - upload_method = "http_put" | "tus_resumable" (based on file size)
5. Backend creates media record with metadata
6. Backend generates upload URL/config
7. Frontend receives upload configuration
```

### Phase 2: File Upload to Storage
```pseudocode
IF file_size <= 6MB:
    Frontend uses HTTP PUT upload
ELSE:
    Frontend uses TUS resumable upload:
    - Create TUS session with metadata
    - Upload in 6MB chunks with progress tracking
    - Handle pause/resume functionality
```

### Phase 3: Webhook-Triggered Processing
```pseudocode
1. Supabase Storage triggers webhook on upload completion
2. Backend /webhooks/upload-complete receives:
   - object_name: "clients/{client_id}/uploads/{filename}"
   - bucket_name: "sermons"
3. Backend discovers media record from filename + client_id
4. Backend reads stored file_category from media.metadata
5. Smart routing based on file_category:
   IF audio: start_audio_transcription_background()
   IF video: start_video_processing_background()
```

### Phase 4: Background Transcription
```pseudocode
FOR AUDIO FILES:
1. Generate signed URL from Supabase Storage
2. Create transcript record (status="processing")
3. Call Deepgram API with signed URL
4. Update transcript with request_id
5. Deepgram processes file directly from Supabase
6. Results saved via callback/polling

FOR VIDEO FILES:
1. Download video from Supabase Storage
2. Extract audio using FFmpeg
3. Upload extracted audio to Supabase Storage
4. Generate signed URL for audio file
5. Create transcript record (status="processing")
6. Call Deepgram API with audio signed URL
7. Continue as audio flow...
```

## 🔧 Critical Functions & Methods

### File Type Detection & Validation
**Location:** `app/services/file_type_service.py`
```python
def detect_file_category(content_type: str) -> FileCategory:
    """Determines if file is AUDIO, VIDEO, or unsupported"""
    
def get_processing_requirements(content_type: str) -> Dict:
    """Returns processing config:
    - processing_type: "direct_audio" | "video_with_audio_extraction"
    - needs_audio_extraction: bool
    - needs_video_upload: bool
    - supports_transcription: bool
    """
```

### Upload Preparation
**Location:** `app/api/endpoints/transcription.py`
```python
@router.post("/upload/prepare")
async def prepare_upload(request: PrepareUploadRequest, auth: AuthContext):
    """
    1. Validates file metadata (no file upload yet)
    2. Creates media record in 'preparing' state
    3. Generates TUS config or HTTP PUT URL
    4. Returns upload configuration to frontend
    """
```

### TUS Configuration Generation
**Location:** `app/services/tus_upload_service.py`
```python
def generate_tus_config(
    upload_url: str, 
    storage_path: str, 
    auth_token: str,
    chunk_size: int = 6MB
) -> TUSConfig:
    """Generates TUS resumable upload configuration with:
    - Metadata (base64 encoded for TUS protocol)
    - Headers (Authorization, tus-resumable, x-upsert)
    - Chunk size and retry configuration
    """
```

### Webhook Processing & Smart Routing
**Location:** `app/api/endpoints/transcription.py`
```python
@router.post("/webhooks/upload-complete")
async def handle_upload_complete(request: Request):
    """
    1. Parses Supabase Storage webhook payload
    2. Discovers media record from object_name
    3. Routes to appropriate background processor
    """

async def start_audio_transcription_background(
    media_id: str, 
    storage_path: str, 
    client_id: str, 
    user_id: str
):
    """Direct audio processing - no extraction needed"""

async def start_video_processing_background(
    media_id: str, 
    storage_path: str, 
    client_id: str, 
    user_id: str
):
    """Video processing with audio extraction"""
```

### Deepgram Integration
**Location:** `app/services/deepgram_service.py`
```python
async def transcribe_from_url(self, signed_url: str) -> Dict[str, Any]:
    """
    Sends signed URL to Deepgram for transcription
    - Deepgram downloads file directly from Supabase
    - Backend never handles file data
    - Returns request_id for tracking
    """
```

### Signed URL Generation
**Location:** `app/services/supabase_service.py`
```python
async def get_signed_url(
    self, 
    bucket: str, 
    path: str, 
    expires_in: int = 3600
) -> str:
    """Generates temporary signed URL for Deepgram access"""
```

## 🗄️ Database Schema Relationships

### Core Tables & Relationships
```sql
users (id, email, ...)
  ↓ 1:N
client_users (user_id, client_id)
  ↓ N:1
clients (id, name, ...)
  ↓ 1:N
media (
  id, 
  filename, 
  storage_path, 
  client_id, 
  user_id,
  metadata: {
    file_category: "audio" | "video",
    processing_requirements: {...},
    upload_status: "preparing" | "completed"
  }
)
  ↓ 1:N
transcripts (
  id,
  video_id (FK to media.id),
  client_id,
  status: "pending" | "processing" | "completed" | "failed",
  request_id (Deepgram tracking),
  content: { full_transcript, utterances, confidence }
)
```

## 🛣️ API Endpoints

### Upload Flow
- `POST /api/v1/transcription/upload/prepare` - Validate & prepare upload
- `POST /api/v1/transcription/webhooks/upload-complete` - Process completed uploads

### File Management  
- `GET /api/v1/transcription/videos` - List user's media files
- `GET /api/v1/transcription/transcripts` - List user's transcripts

### Transcription Status
- `GET /api/v1/transcription/status/{transcript_id}` - Check transcription status
- `GET /api/v1/transcription/{transcript_id}` - Get transcript content

## ⚙️ Configuration & Settings

### File Size Routing
```python
TUS_THRESHOLD = 6 * 1024 * 1024  # 6MB
# Files > 6MB use TUS resumable upload
# Files ≤ 6MB use HTTP PUT upload
```

### TUS Configuration
```python
TUS_CHUNK_SIZE = 6 * 1024 * 1024  # 6MB chunks
TUS_MAX_RETRIES = 3
TUS_RETRY_DELAY = 1000  # milliseconds
```

### File Validation Limits
```python
MAX_FILE_SIZE = 50 * 1024 * 1024 * 1024  # 50GB
SUPPORTED_TYPES = ["audio/*", "video/*"]
```

## 🔐 Security & Authentication

### JWT Token Flow
1. User authenticates → JWT token issued
2. Token contains `user_id` and client context
3. All API calls require `Authorization: Bearer {token}`
4. Backend validates token and extracts user context

### Client Relationship Enforcement
```python
# Every upload requires client association
client = await supabase_service.get_user_client(auth.user.id)
if not client:
    raise HTTPException(400, "User must belong to a client")

# All media records linked to client_id
media = MediaCreate(
    client_id=client.id,
    user_id=auth.user.id,
    # ... other fields
)
```

## 📊 Monitoring & Observability

### Key Metrics to Track
- Upload success/failure rates by file size
- TUS vs HTTP PUT usage distribution  
- Transcription completion times
- Deepgram API response times
- Storage space usage per client

### Critical Log Points
```python
# Upload preparation
logger.info(f"File category detected: {file_category.value}")
logger.info(f"Upload method: {upload_method}")

# Webhook processing
logger.info(f"📋 Processing upload completion for {file_category} file")
logger.info(f"🎵 Starting audio processing pipeline")

# Deepgram integration
logger.info(f"✅ Deepgram transcription started: {result.get('request_id')}")
```

## 🧪 Testing Strategy

### Test Coverage
1. **Unit Tests** (`test_tus_config_unit.py`) - TUS configuration logic
2. **Integration Tests** (`test_tus_upload_integration.py`) - Real API calls
3. **End-to-End Tests** (`test_transcription_pipeline.py`) - Full workflow
4. **Frontend Tests** (`test_frontend_tus.html`) - Browser-based TUS upload

### Critical Test Scenarios
- File size routing (6MB threshold)
- TUS metadata encoding (base64)
- Error handling and validation
- Client relationship enforcement
- Webhook trigger simulation

## 🚨 Common Issues & Debugging

### TUS Upload Failures
- **"Invalid tus-resumable"** → Frontend passing conflicting headers
- **"Invalid upload-metadata"** → Metadata not base64 encoded
- **Duplicate key violation** → Filename conflicts, add timestamps

### Webhook Not Triggering
- **Supabase webhook configuration** → Must be manually configured
- **ngrok URL changes** → Update webhook endpoint in Supabase
- **File not found** → Check storage path format

### Transcription Failures
- **No signed URL** → Check Supabase service role permissions
- **Deepgram timeout** → Verify file accessibility from Deepgram
- **Audio extraction fails** → FFmpeg dependency issues

## 🔄 Development Commands

### Run Tests
```bash
# Unit tests
python -m pytest test_tus_config_unit.py -v

# Integration tests  
python test_tus_upload_integration.py

# End-to-end pipeline
python test_transcription_pipeline.py

# Frontend test
open test_frontend_tus.html
```

### Generate Fresh Token
```bash
python generate_fresh_token.py
```

### Manual Webhook Trigger
```bash
curl -X POST "http://localhost:8000/api/v1/transcription/webhooks/upload-complete" \
  -H "Content-Type: application/json" \
  -d '{"object_name": "path/to/file.mp3", "bucket_name": "sermons"}'
```

---

**This system successfully handles:**
- ✅ Large file uploads (86MB+) with TUS resumable protocol
- ✅ Smart routing between audio and video processing
- ✅ Direct Deepgram integration via signed URLs
- ✅ Complete audit trails and client isolation
- ✅ Real-time progress tracking and error handling
- ✅ Production-ready scalability and monitoring