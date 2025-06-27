# Concurrent Audio Extraction Testing Guide

## Overview

This guide covers testing the concurrent audio extraction feature that enables immediate transcription while video uploads continue in the background.

## Feature Summary

**Problem Solved:** Large sermon videos (4GB-40GB) took 45+ minutes to upload before transcription could begin.

**Solution:** Extract audio concurrently with video upload, start transcription immediately from audio, continue video upload in background.

**Expected Outcome:** 60% faster transcript access (25 minutes vs 45+ minutes) for content creation.

## Testing Strategy

### Core Functionality Focus
- **Does it work?** (not "is it faster?")
- **Does error handling work?**
- **Does cleanup work?**
- **Does the flow match requirements?**

## Test Suite Structure

### 1. End-to-End Testing (`run_quick_test.py`)

**Purpose:** Verify complete user workflow with concurrent processing

**Key Verifications:**
```bash
python run_quick_test.py
```

**What it tests:**
- User registration → Concurrent upload → Transcription → Callback → Cleanup
- Response structure indicates concurrent processing
- Audio extraction completed before response
- Video upload marked as "background_processing"
- Audio cleanup after successful transcription

**Success Indicators:**
```
✅ PASS Concurrent Upload + Audio Extraction
✅ PASS Callback + Audio Cleanup
🎉 ALL TESTS PASSED! Complete concurrent audio extraction flow working!
```

### 2. Unit Tests (`test_audio_extraction_service.py`)

**Purpose:** Test audio extraction service in isolation

```bash
pytest tests/test_audio_extraction_service.py -v
```

**Core Functions Tested:**
- `extract_and_upload_audio()` - Main extraction workflow
- `cleanup_audio_file()` - Storage cleanup
- `_run_ffmpeg_extraction()` - FFmpeg parameters
- Error handling and stream management

**Key Test Cases:**
```python
test_extract_audio_from_small_file()        # Basic functionality
test_ffmpeg_extraction_error_handling()     # Graceful failures
test_supabase_upload_error_handling()       # Upload failures
test_stream_position_reset()                # Video reuse
test_cleanup_audio_file_success()           # Storage cleanup
test_ffmpeg_command_parameters()            # Deepgram optimization
```

### 3. Integration Tests (`test_concurrent_upload_flow.py`)

**Purpose:** Test concurrent processing flow and error scenarios

```bash
pytest tests/test_concurrent_upload_flow.py -v
```

**Critical Flow Tests:**
```python
test_transcription_starts_immediately_not_waiting_for_video()  # Key requirement
test_audio_extraction_failure_cancels_video_upload()          # Complete failure
test_background_video_upload_independence()                   # Fire-and-forget
test_callback_audio_cleanup_integration()                     # End-to-end cleanup
test_concurrent_flow_response_structure()                     # API contract
```

## Test Scenarios

### Scenario A: Happy Path (Test with test_audio.mp4)
```
1. Upload test_audio.mp4 video file (~44MB)
2. ✅ Audio extracted and uploaded immediately
3. ✅ Transcription starts from audio
4. ✅ Response returned quickly
5. ✅ Video upload continues in background
6. ✅ Transcript ready shortly after
7. ✅ Audio file cleaned up after completion
```

**Note:** Using `test_audio.mp4` provides faster testing while demonstrating the same concurrent processing functionality as larger files.

### Scenario B: Audio Extraction Failure
```
1. Upload corrupted video file
2. ❌ Audio extraction fails
3. ✅ Video upload task cancelled
4. ✅ Complete failure response to user
5. ✅ No partial success state
```

### Scenario C: Error Recovery
```
1. Upload valid video
2. ✅ Audio extracted successfully
3. ✅ Transcription starts
4. ❌ Video upload fails (network issue)
5. ✅ Transcription continues (independent)
6. ✅ User gets transcript despite video failure
```

## Response Verification

### Expected Upload Response Structure
```json
{
  "success": true,
  "message": "Audio extracted and transcription started immediately. Video upload continues in background.",
  "processing_info": {
    "audio_extracted": true,
    "transcription_started": true,
    "video_upload_status": "background_processing"
  },
  "next_steps": {
    "description": "Transcription processing from extracted audio (faster than full video)",
    "estimated_time": "~6 minutes"
  }
}
```

### Key Response Indicators
- ✅ Message mentions "Audio extracted" and "transcription started immediately"
- ✅ `processing_info.audio_extracted = true`
- ✅ `processing_info.transcription_started = true`
- ✅ `processing_info.video_upload_status = "background_processing"`
- ✅ Description mentions "extracted audio"

## Audio Cleanup Verification

### Callback Processing
```json
POST /api/v1/transcription/callback
{
  "metadata": {"request_id": "deepgram-123"},
  "results": {"channels": [{"alternatives": [{"transcript": "..."}]}]}
}
```

### Expected Cleanup Logs
```
✅ Transcript updated successfully - Status: completed
🧹 Cleaned up audio file: clients/{client_id}/audio/audio_{video_id}_{hash}.wav
```

## Manual Testing Checklist

### Pre-Test Setup
- [ ] Test video file available (use `test_audio.mp4` - ~44MB, faster for testing)
- [ ] Environment variables configured
- [ ] Supabase storage accessible
- [ ] Deepgram API key valid

**Note:** `test_audio.mp4` is perfect for testing as it's large enough to trigger TUS resumable upload (>6MB threshold) while being small enough for fast testing cycles.

### Test Execution
- [ ] Run `python run_quick_test.py`
- [ ] Verify concurrent processing response structure
- [ ] Check logs for audio extraction and upload
- [ ] Verify transcription starts immediately
- [ ] Simulate callback and verify cleanup

### Success Criteria
- [ ] Upload response indicates concurrent processing
- [ ] Transcription request_id returned immediately
- [ ] Video upload continues in background
- [ ] Audio file cleaned up after transcription
- [ ] No orphaned temporary files

## Troubleshooting

### Common Issues

**Audio extraction fails:**
- Check FFmpeg installation: `ffmpeg -version`
- Verify test_audio.mp4 file exists and has audio stream
- Check temporary directory permissions

**Upload response doesn't show concurrent processing:**
- Verify audio extraction service import
- Check for exceptions in upload endpoint
- Review logs for service initialization

**Audio cleanup doesn't work:**
- Check Supabase storage permissions
- Verify metadata storage in transcript record
- Review callback logs for cleanup attempts

**Tests fail with mocking errors:**
- Ensure all async functions properly mocked
- Check patch decorators target correct modules
- Verify mock return values match expected types

### Debug Commands
```bash
# Check service imports
python -c "from app.services.audio_extraction_service import audio_extraction_service; print('OK')"

# Test FFmpeg availability
ffmpeg -version

# Run specific test with verbose output
pytest tests/test_concurrent_upload_flow.py::TestConcurrentUploadFlow::test_transcription_starts_immediately_not_waiting_for_video -v -s

# Run tests with full traceback
pytest tests/ -v --tb=long
```

## Performance Notes

**What we DON'T test:**
- Timing comparisons (audio vs video speed)
- Performance benchmarks
- Multiple concurrent uploads

**Focus:** Functional verification only - does the concurrent flow work as designed?

## Expected Test Results

### All Tests Passing (with test_audio.mp4)
```
🔹 Using real file: test_audio.mp4
   File size: 44.12MB
   Upload method: TUS resumable (threshold: 6.0MB)

🔍 CONCURRENT PROCESSING VERIFICATION:
   ✅ Message indicates concurrent processing: Audio extracted and transcription started immediately. Video upload continues in background.
   ✅ Processing info present
   ✅ Audio extracted: True
   ✅ Transcription started: True
   ✅ Video upload in background: background_processing
   ✅ Next steps mention audio extraction: Transcription processing from extracted audio (faster than full video)

🎉 ALL TESTS PASSED! Complete concurrent audio extraction flow working!

✅ Your implementation successfully:
   • Creates users and organizations
   • Extracts audio concurrently with video upload
   • Starts transcription immediately from audio
   • Routes large files to TUS resumable upload (background)
   • Processes callback responses with audio cleanup
   • Stores and retrieves transcript content
   • Provides API endpoints for frontend integration
```

### Test Metrics
- **Unit Tests:** 12+ test cases covering core functionality
- **Integration Tests:** 8+ test cases covering flow scenarios
- **End-to-End Tests:** 6 phases covering complete user workflow

## Next Steps

After successful testing:
1. Deploy to staging environment
2. Test with real video files
3. Monitor audio cleanup in production logs
4. Gather user feedback on transcript speed improvement

## Additional Resources

- [GitHub Issue #3](https://github.com/jaredjohnston/sermon-ai-backend/issues/3) - Original requirements
- [Audio Extraction Service](app/services/audio_extraction_service.py) - Core implementation
- [Upload Endpoint](app/api/endpoints/transcription.py) - Concurrent flow logic
- [Quick Test Runner](run_quick_test.py) - End-to-end verification