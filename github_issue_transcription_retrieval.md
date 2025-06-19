# GitHub Issue: Add transcription retrieval and status endpoints

**Status:** Ready to create  
**Label:** enhancement  
**Priority:** High  
**Estimated Effort:** 8-10 hours  

---

## Problem Statement

Currently, users can upload videos and start transcription jobs through the `/api/v1/transcription/upload` endpoint, but they have no way to:

- View completed transcription results
- Check the status of in-progress transcription jobs  
- Retrieve historical transcripts for their videos
- Access transcription data after the initial upload response

The `/api/v1/transcription/status/{transcript_id}` endpoint exists but only returns a placeholder response (see `app/api/endpoints/transcription.py:148-175`). The callback endpoint receives Deepgram results but doesn't update the database with the actual transcription content.

This creates a poor user experience where transcription data is processed but never accessible to users who submitted it.

## Proposed Solution

Implement a complete set of transcription retrieval endpoints that allow authenticated users to:

1. **Check transcription job status** - Get real-time status of processing jobs
2. **View completed transcripts** - Retrieve full transcription content with metadata
3. **List user transcripts** - Browse all transcripts for their organization
4. **Access transcript history** - Retrieve transcripts by video or time range

The solution will extend the existing FastAPI/Supabase architecture and follow established patterns for authentication, multi-tenancy, and error handling.

## Technical Details

### **Missing Service Methods (SupabaseService)**

The following methods need to be added to `app/services/supabase_service.py`:

```python
async def get_transcript(transcript_id: UUID) -> Optional[Transcript]
async def get_user_transcripts(user_id: UUID) -> List[Transcript] 
async def get_video_transcript(video_id: UUID) -> Optional[Transcript]
async def get_transcript_with_video(transcript_id: UUID) -> Optional[Dict[str, Any]]
```

### **Critical Prerequisite**
Fix the missing `_get_client()` method referenced in 13 locations in the service (should likely alias `_get_service_client()`).

### **API Endpoints to Implement/Complete**

1. **`GET /api/v1/transcription/status/{transcript_id}`** - Complete the placeholder implementation
2. **`GET /api/v1/transcription/{transcript_id}`** - Retrieve full transcript content  
3. **`GET /api/v1/transcription/`** - List user's transcripts with pagination
4. **`GET /api/v1/transcription/video/{video_id}`** - Get transcript for specific video

### **Database Schema Reference**

Based on `app/models/schemas.py`, the Transcript model includes:
- `status: TranscriptStatus` (processing/completed/failed/pending)
- `raw_transcript: Optional[Dict[str, Any]]` - Deepgram raw response
- `processed_transcript: Optional[Dict[str, Any]]` - Processed/formatted content
- `request_id: Optional[str]` - Deepgram correlation ID
- Standard audit fields (created_at, created_by, client_id, etc.)

### **Authentication & Authorization**
- Follow existing JWT Bearer token pattern (`app/middleware/auth.py`)
- Implement client-scoped access (users can only access their organization's transcripts)
- Use existing `get_current_user` dependency injection
- Maintain Row Level Security (RLS) compliance

### **Enhanced Callback Processing**
Update `/api/v1/transcription/callback` endpoint to:
- Parse Deepgram response and extract transcript content
- Update transcript record with results and status
- Handle error cases and failed transcriptions

## Implementation Plan

### **Phase 1: Service Layer Foundation** (2-3 hours)
1. **Fix `_get_client()` method** in SupabaseService 
2. **Add `get_transcript(transcript_id)`** method with proper error handling
3. **Add `get_user_transcripts(user_id)`** method with client filtering
4. **Add `get_video_transcript(video_id)`** method 
5. **Add `get_transcript_with_video(transcript_id)`** method with JOIN query

### **Phase 2: API Endpoints** (3-4 hours)  
1. **Complete `/status/{transcript_id}` endpoint** using new service methods
2. **Implement `/transcription/{transcript_id}` endpoint** for full transcript retrieval
3. **Implement `/transcription/` endpoint** with pagination and filtering
4. **Implement `/transcription/video/{video_id}` endpoint** for video-specific transcripts
5. **Add proper error handling** following existing patterns (`400/401/404/500` status codes)

### **Phase 3: Callback Enhancement** (1-2 hours)
1. **Parse Deepgram callback response** in `/callback` endpoint  
2. **Extract transcript content** from response structure
3. **Update transcript record** with `raw_transcript` and `processed_transcript`
4. **Update status** to `completed` or `failed` based on response
5. **Add error handling** for malformed callbacks

### **Phase 4: Validation & Testing** (2-3 hours)
1. **Add input validation** for transcript IDs and filters
2. **Test multi-tenant isolation** (users can't access other clients' transcripts)
3. **Test error scenarios** (invalid IDs, missing transcripts, failed jobs)
4. **Integration testing** with real Deepgram responses
5. **Performance testing** with large transcript payloads

## Acceptance Criteria

### **Functional Requirements**
- [ ] Users can check transcription job status by transcript ID
- [ ] Users can retrieve complete transcript content when job is completed  
- [ ] Users can list all their organization's transcripts
- [ ] Users can get transcript for a specific video
- [ ] Callback endpoint properly updates transcript records with Deepgram results
- [ ] All endpoints require authentication and respect client boundaries

### **Technical Requirements**  
- [ ] All endpoints return consistent response formats matching existing patterns
- [ ] Proper HTTP status codes for success/error scenarios
- [ ] Multi-tenant security enforced (users only access their client's data)
- [ ] Error messages are user-friendly and don't expose internal details
- [ ] Database queries use soft-delete filtering (`deleted_at IS NULL`)
- [ ] Performance acceptable for transcripts up to 1 hour of audio content

### **Response Format Examples**

**Status Endpoint:**
```json
{
  "transcript_id": "uuid",
  "status": "completed|processing|failed|pending", 
  "video_id": "uuid",
  "created_at": "timestamp",
  "estimated_completion": "timestamp|null",
  "error_message": "string|null"
}
```

**Transcript Content Endpoint:**
```json
{
  "transcript_id": "uuid",
  "video": {
    "id": "uuid",
    "filename": "sermon.mp4", 
    "duration_seconds": 1800
  },
  "status": "completed",
  "content": {
    "full_transcript": "string",
    "utterances": [{"speaker": 0, "text": "...", "start": 1.2, "end": 4.5}],
    "confidence": 0.95
  },
  "created_at": "timestamp",
  "completed_at": "timestamp"
}
```

## Additional Considerations

### **Performance Implications**
- Large transcript payloads (1+ hour sermons) may require pagination for utterance lists
- Consider implementing transcript excerpt/summary endpoints for dashboard views
- Database queries should use appropriate indexes on `client_id`, `user_id`, and `video_id`

### **Security Considerations**  
- Transcript content may be sensitive religious content requiring careful access control
- Ensure audit logs capture transcript access for compliance
- Consider implementing transcript sharing/permissions for team members

### **Integration Impact**
- This completes the core backend transcription workflow started in the upload endpoint
- Frontend can now build transcript viewing dashboards using these endpoints
- May need rate limiting for transcript listing endpoints to prevent abuse

### **Documentation Updates**
- Add API documentation for all new endpoints
- Update SYSTEM_AUTOPSY.md to reflect completed transcription retrieval capabilities  
- Add usage examples to help frontend integration

### **Future Enhancements**
- Real-time status updates via WebSocket connections
- Transcript search and keyword highlighting
- Export functionality (PDF, DOCX, etc.)
- Transcript editing and annotation features

---

## How to Create This Issue

1. Go to your GitHub repository
2. Click "Issues" → "New Issue"  
3. Copy the content above (excluding this section)
4. Title: "Add transcription retrieval and status endpoints"
5. Add label: `enhancement`
6. Submit

## Implementation Notes

- This addresses priority #1 from SYSTEM_AUTOPSY.md
- Follows existing FastAPI/Supabase patterns from codebase analysis
- Maintains multi-tenant security model
- Enables frontend development with stable API contracts