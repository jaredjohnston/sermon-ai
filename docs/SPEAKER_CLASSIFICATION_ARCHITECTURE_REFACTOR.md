# Speaker Classification Architecture Refactor Proposal

## Problem Analysis

The current implementation violates webhook best practices by doing heavy processing (OpenAI API calls) inside the webhook handler, causing timeouts, retries, and architectural issues.

## Root Cause Issues

### 1. **Anti-Pattern**: Heavy AI processing in webhook
- **Current**: Webhook takes 2-5 seconds due to OpenAI API calls
- **Should be**: Webhook should complete in <100ms
- **Impact**: Causes timeouts, retries, and callback loops

### 2. **Mixed Concerns**: Conflating Deepgram transcription status with OpenAI processing status
- **Current**: Single `status` field represents both Deepgram AND OpenAI success
- **Should be**: Separate status fields for each concern
- **Impact**: OpenAI failures make entire transcript "failed"

### 3. **Large Payloads**: Storing massive data in single HTTP request
- **Current**: Entire Deepgram response + AI results in one update
- **Should be**: Split into smaller, manageable updates
- **Impact**: HTTP/2 frame limit errors (`httpcore.LocalProtocolError: 41`)

### 4. **Poor Separation**: Single failure point affects both transcription and classification
- **Current**: If OpenAI fails, entire process fails
- **Should be**: Independent failure modes with proper isolation
- **Impact**: Reduces system reliability and makes debugging difficult

## Proposed Architecture Refactor

### 1. Implement Proper Webhook Pattern (Critical)

**Current Flow:**
```
Deepgram Callback → Validate → OpenAI API → Store Results → Return Response
     30s timeout      fast        2-5s         large          slow
```

**Proposed Flow:**
```
Deepgram Callback → Validate → Store Raw → Queue Job → Return 200 OK
     30s timeout      fast       fast       fast      <100ms

Background Job → OpenAI API → Store Results → Update Status
   no timeout       2-5s        any size     independent
```

### 2. Separate Status Fields (High Priority)

**Current Schema:**
```python
class Transcript:
    status: str  # "pending", "processing", "completed", "failed"
    # Single status for both Deepgram AND OpenAI
```

**Proposed Schema:**
```python
class Transcript:
    status: str              # Deepgram transcription status
    processing_status: str   # OpenAI classification status
```

**Status Values:**
- `transcript.status = "completed"` when Deepgram provides raw transcript
- `transcript.processing_status = "pending"` when OpenAI processing not started
- `transcript.processing_status = "processing"` when OpenAI API calls in progress
- `transcript.processing_status = "completed"` when AI classification finished
- `transcript.processing_status = "failed"` when OpenAI processing fails

### 3. Background Job Queue (High Priority)

**Webhook Handler:**
```python
@router.post("/callback")
async def transcription_callback(request: Request):
    # ✅ Fast validation only
    # ✅ Store raw transcript
    # ✅ Set transcript.status = "completed"
    # ✅ Set transcript.processing_status = "pending"
    # ✅ Queue background classification job
    # ✅ Return 200 OK immediately (no OpenAI calls)
```

**Background Job:**
```python
async def process_speaker_classification(transcript_id):
    # ✅ Set processing_status = "processing"
    # ✅ Run OpenAI classification
    # ✅ Store processed_transcript
    # ✅ Set processing_status = "completed" or "failed"
    # ✅ Handle retries independently
    # ✅ No webhook timeouts
```

### 4. Optimize Data Storage (Medium Priority)

**Current Issue:**
- Storing entire Deepgram response + AI results + metadata in single PATCH request
- Large JSON payloads exceeding HTTP/2 frame limits

**Proposed Solution:**
- Store raw transcript in webhook (small, fast)
- Store processed results in background job (large, no time pressure)
- Split updates into smaller chunks if needed

## Implementation Plan

### Phase 1: Database Schema Updates
1. Add `processing_status` field to transcripts table
2. Update data models and schemas
3. Maintain backward compatibility

### Phase 2: Webhook Refactor
1. Simplify webhook to store raw transcript only
2. Queue background job for AI processing
3. Return fast responses to Deepgram

### Phase 3: Background Processing
1. Implement background job queue
2. Move OpenAI classification to background
3. Update status fields appropriately

### Phase 4: Integration & Testing
1. Test webhook performance (<100ms)
2. Verify background processing works
3. Monitor error rates and retry logic

## Expected Benefits

### Reliability
- ✅ Webhook never times out (fast response)
- ✅ Deepgram retries stop immediately (proper 200 OK)
- ✅ OpenAI failures don't affect transcription status
- ✅ Proper error isolation between services

### Performance
- ✅ Fast webhook responses (<100ms vs 2-5 seconds)
- ✅ No HTTP/2 payload issues
- ✅ Background processing can take unlimited time
- ✅ Better resource utilization

### Maintainability
- ✅ Clear separation of concerns
- ✅ Easier to debug transcription vs classification issues
- ✅ Independent retry logic for each service
- ✅ Follows conventional webhook patterns

### Scalability
- ✅ Background job queue can handle load spikes
- ✅ Independent scaling of transcription vs classification
- ✅ Better error recovery mechanisms

## Migration Strategy

### Backward Compatibility
- Keep existing `status` field during transition
- Add new `processing_status` field alongside
- Update ContentService to work with both patterns
- Gradual rollout with feature flags

### Monitoring
- Track both old and new status fields
- Monitor webhook response times
- Alert on background job failures
- Measure improvement in callback success rates

### Rollback Plan
- Maintain ability to fall back to current implementation
- Database migrations should be reversible
- Feature flags for easy toggles

## Anti-Pattern Rule

**DON'T DO**: Heavy processing (API calls, complex computations) inside webhook handlers

**DO**: Acknowledge quickly, queue background jobs, process asynchronously

This architectural change addresses the root cause rather than patching symptoms, following conventional webhook best practices and proper separation of concerns.