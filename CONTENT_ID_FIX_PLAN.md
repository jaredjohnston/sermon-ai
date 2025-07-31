# Clean Architecture Fix for Content ID Consistency

## Problem Summary
The content library shows uploads during the session but they disappear on page refresh. This happens because:
- Upload flow uses `media_id` as the primary identifier
- List/refresh flow uses `transcript_id` as the primary identifier  
- Same asset has two different IDs, causing the frontend to lose track

## Core Architecture Principles
1. **Media is the parent entity** - all uploads create a `media` record with `media_id`
2. **Transcripts are optional children** - only audio/video files create a `transcript` record
3. **Document files (DOCX, PDF) skip transcription** - they only have `media_id`, no `transcript_id`
4. **Use consistent primary identifier** - `media_id` should be used for all content types

## Current ID Flow Analysis

### Upload Flow
1. User uploads file → Creates `media` record with `media_id`
2. Frontend receives `media_id` and uses it as `ContentSource.id`
3. For audio/video: Background process creates `transcript` record with:
   - `transcript.id` (its own ID)
   - `transcript.video_id` (foreign key to `media.id` - poorly named!)

### List/Refresh Flow  
1. Dashboard calls `listTranscripts()` API
2. Backend returns transcript records
3. `data-transformers.ts:59` sets `ContentSource.id = transcript.transcript_id`
4. Content "disappears" because frontend is now using different IDs!

## Implementation Plan

### Phase 1: Fix Data Transformer (Immediate Fix)
**Goal**: Stop content from disappearing on page refresh

1. Update `frontend/lib/data-transformers.ts` line 59:
   ```typescript
   // Current (broken):
   id: transcript.transcript_id,
   
   // Fixed:
   id: transcript.video_id,  // This is actually media_id!
   ```

2. This immediately fixes the disappearing content issue
3. Test with both audio/video uploads and page refreshes

### Phase 2: Clean Up Response Types
**Goal**: Make the API responses clearer and more consistent

1. Add `media_id` field to `TranscriptResponse` interface in `shared/types/api.ts`
2. Update backend to explicitly include `media_id` in responses
3. Consider renaming `video_id` → `media_id` in the response types
4. Ensure all API responses include both IDs for clarity:
   - `media_id`: Primary identifier for all content
   - `transcript_id`: Secondary identifier for transcript-specific operations

### Phase 3: Database Schema Cleanup
**Goal**: Fix the confusing `video_id` naming

1. Create database migration to rename `transcripts.video_id` → `transcripts.media_id`
2. Update all foreign key constraints
3. Update indexes for performance
4. Test migration on development database first
5. Update backend models to reflect new column name

### Phase 4: API Endpoint Restructuring  
**Goal**: Better reflect that endpoints handle all content types, not just transcriptions

1. Plan new endpoint structure:
   - Current: `/api/v1/transcription/*`
   - New: `/api/v1/media/*` or `/api/v1/sermon/*`
2. Consider existing `content.py` to avoid conflicts
3. Create new endpoints with proper naming
4. Migrate frontend to use new endpoints
5. Deprecate old endpoints gracefully

### Phase 5: Simplify Polling Logic
**Goal**: Remove complex workarounds now that IDs are consistent

1. Remove media→transcript ID resolution in dashboard polling
2. Use consistent `media_id` throughout polling logic
3. Simplify status checking code
4. Remove any ID mapping/translation logic
5. Test with various file types and processing states

## Future Considerations

### Supporting Document Types
When adding DOCX/PDF support:
- These files will only have `media_id` (no transcript needed)
- Status flow: `upload → processing → ready_for_content_generation`
- Content generation will work directly with extracted text, not transcripts

### Unified Content View
Consider creating a Supabase view that joins media + transcripts:
- Single source of truth for all content
- Consistent field naming
- Handles both transcribed and non-transcribed content gracefully

## Testing Checklist
- [ ] Upload audio file, verify it appears in library
- [ ] Upload video file, verify it appears in library  
- [ ] Refresh page, verify all content still appears
- [ ] Check that transcription status updates work
- [ ] Verify content generation works with new ID system
- [ ] Test with multiple uploads in parallel
- [ ] Verify polling doesn't create duplicate entries

## Notes
- The root cause is using different IDs for the same entity
- `media_id` is the logical primary identifier since all content has it
- `transcript_id` should be kept but used only for transcript-specific operations
- This fix maintains backward compatibility while setting up for future document support