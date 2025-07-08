# 👀 Supabase Verification Checklist for TUS Upload

## 🎯 Purpose
After uploading your 86MB file using TUS, use this checklist to verify everything worked correctly in Supabase. This is **real-world verification** where you visually confirm the system integration.

---

## 📋 Pre-Upload Information
Before starting, note these details from your upload test:

- **Media ID**: `_________________` (from prepare response)
- **File Name**: `_________________` (your test filename)
- **File Size**: `86,988,483 bytes` (86MB exactly)
- **Expected Path**: `clients/{client-id}/uploads/{filename}.mp3`
- **Upload Method**: `tus_resumable` (for 86MB file)
- **Chunk Size**: `6,291,456 bytes` (6MB chunks)
- **Expected Chunks**: `~14 chunks` (86MB ÷ 6MB)

---

## 🗄️ **STEP 1: Supabase Storage Verification**

### **Navigate to Storage**
1. Open [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Storage** in left sidebar
4. Click on **`sermons`** bucket

### **Locate Your File**
```
Expected path structure:
sermons/
  └── clients/
      └── {client-id}/
          └── uploads/
              └── {your-filename}.mp3
```

### **Verify File Details**
- [ ] **File exists** at expected path
- [ ] **File size**: Exactly `86,988,483 bytes` (86MB)
- [ ] **Upload date**: Recent timestamp
- [ ] **File type**: `audio/mpeg` or similar
- [ ] **Download test**: Try downloading file (should match original)

### **Visual Confirmation**
Take a screenshot showing:
- File in correct bucket location
- File size matching expected bytes
- Recent upload timestamp

---

## 🗃️ **STEP 2: Database Tables Verification**

### **Media Table Check**
Navigate to **Database** → **Table Editor** → **`media`** table

**Find your record by Media ID**: `{your-media-id}`

Verify these fields:
- [ ] **`id`**: Matches your Media ID
- [ ] **`filename`**: Matches your test filename
- [ ] **`content_type`**: `audio/mpeg`
- [ ] **`size_bytes`**: `86988483`
- [ ] **`storage_path`**: `clients/{client-id}/uploads/{filename}.mp3`
- [ ] **`client_id`**: Valid UUID (not null)
- [ ] **`created_at`**: Recent timestamp
- [ ] **`created_by`**: Valid user UUID (not null)
- [ ] **`updated_at`**: Recent timestamp
- [ ] **`updated_by`**: Valid user UUID (not null)
- [ ] **`deleted_at`**: NULL
- [ ] **`deleted_by`**: NULL

**Metadata Field Check**:
```json
{
  "file_category": "audio",
  "processing_requirements": {
    "processing_type": "direct_audio",
    "needs_audio_extraction": false,
    "needs_video_upload": false
  },
  "upload_status": "completed",
  "upload_method": "direct_to_supabase"
}
```

### **Transcripts Table Check**
Navigate to **Database** → **Table Editor** → **`transcripts`** table

**Find record by video_id**: `{your-media-id}`

Verify these fields:
- [ ] **`id`**: Valid transcript UUID
- [ ] **`video_id`**: Matches your Media ID
- [ ] **`client_id`**: Matches your client ID
- [ ] **`status`**: `processing` → `completed` (or `failed`)
- [ ] **`request_id`**: Deepgram request ID (when transcription starts)
- [ ] **`raw_transcript`**: JSON with Deepgram results (when completed)
- [ ] **`processed_transcript`**: Processing metadata
- [ ] **`error_message`**: NULL (unless failed)
- [ ] **`created_at`**: Recent timestamp
- [ ] **`created_by`**: Valid user UUID (not null)
- [ ] **`updated_at`**: Updates as processing progresses
- [ ] **`updated_by`**: Valid user UUID (not null)

**Metadata Field Check**:
```json
{
  "audio_storage_path": "clients/{client-id}/uploads/{filename}.mp3",
  "processing_type": "direct_audio"
}
```

---

## 🔄 **STEP 3: Processing Pipeline Verification**

### **Timeline Check**
The processing should follow this sequence:

1. **Upload Complete** (`media` record created)
2. **Webhook Triggered** (within seconds)
3. **Transcript Created** (`transcripts` record with status `processing`)
4. **Deepgram Started** (`request_id` added)
5. **Transcription Complete** (status → `completed`, `raw_transcript` populated)

### **Status Progression**
Check transcript status over time:
- [ ] **Initial**: `pending` or `processing`
- [ ] **Processing**: Has `request_id` from Deepgram
- [ ] **Final**: `completed` with transcript content OR `failed` with error

### **Audio File Cleanup**
After transcription completion:
- [ ] **Retention**: Audio file scheduled for cleanup (check `metadata`)
- [ ] **Cleanup date**: Should be `current_date + retention_days`

---

## 🔍 **STEP 4: API Verification** 

### **Status Endpoint Check**
Test the status endpoint:
```bash
curl -H "Authorization: Bearer {your-token}" \
     http://localhost:8000/api/v1/transcription/status/{transcript-id}
```

Expected response:
```json
{
  "transcript_id": "...",
  "video_id": "...",
  "status": "completed",
  "created_at": "...",
  "updated_at": "...",
  "request_id": "..."
}
```

### **Transcript Content Check**
Get full transcript:
```bash
curl -H "Authorization: Bearer {your-token}" \
     http://localhost:8000/api/v1/transcription/{transcript-id}
```

Expected response structure:
```json
{
  "transcript_id": "...",
  "video": {
    "id": "...",
    "filename": "...",
    "size_bytes": 86988483
  },
  "status": "completed",
  "content": {
    "full_transcript": "...",
    "utterances": [...],
    "confidence": 0.95
  }
}
```

---

## 🏆 **STEP 5: Success Criteria**

### **Complete Success** ✅
- [ ] **File uploaded**: 86MB file in Supabase Storage
- [ ] **Database records**: Both `media` and `transcripts` tables populated
- [ ] **Processing complete**: Transcript status = `completed`
- [ ] **Content available**: Transcript text generated by Deepgram
- [ ] **Audit trail**: All `created_by`/`updated_by` fields have valid UUIDs
- [ ] **No errors**: No error messages in database or logs

### **Partial Success** ⚠️
- [ ] **File uploaded** but transcription failed
- [ ] **Database created** but processing stuck
- [ ] **Webhooks working** but Deepgram issues

### **Upload Success, Processing Failed** 🔧
This is still a TUS upload success! The upload verification is complete.
Processing issues are separate from TUS functionality.

---

## 🛠️ **Troubleshooting Common Issues**

### **File Not in Storage**
- Check bucket name (`sermons`)
- Verify path structure
- Check upload actually completed (look for 100% progress)

### **No Database Records**
- Check webhook configuration
- Verify API server received webhook
- Check server logs for webhook processing

### **Wrong Audit Fields**
- Should be user UUID, not `00000000-0000-0000-0000-000000000000`
- Indicates authentication/user context issues

### **Processing Stuck**
- Check Deepgram service status
- Verify Deepgram webhook configuration
- Check network connectivity to Deepgram

---

## 📊 **Verification Summary Template**

```
TUS UPLOAD VERIFICATION RESULTS
===============================

File Upload:
✅/❌ 86MB file uploaded to Supabase Storage
✅/❌ File size matches expected (86,988,483 bytes)
✅/❌ File accessible via Supabase dashboard

Database Records:
✅/❌ Media record created with correct metadata
✅/❌ Transcript record created and processed
✅/❌ Audit fields populated with valid UUIDs

Processing Pipeline:
✅/❌ Webhook triggered successfully
✅/❌ Transcription completed successfully
✅/❌ Content available via API

Overall Result:
🎉 COMPLETE SUCCESS - TUS upload working perfectly
⚠️  PARTIAL SUCCESS - Upload works, processing issues
❌ FAILED - Upload or database issues

Notes:
_________________________________
_________________________________
```

---

## 🎯 **Key Takeaways**

### **TDD vs Real-World Testing**
- **TDD Tests**: Verified the code logic works correctly
- **This Verification**: Confirms the actual system integration works end-to-end
- **Both are essential**: TDD for development speed, real-world for deployment confidence

### **What This Proves**
✅ **TUS resumable uploads** work for large files  
✅ **Frontend direct uploads** bypass API servers  
✅ **Supabase Storage integration** functions correctly  
✅ **Database webhooks** trigger processing pipeline  
✅ **Authentication** maintains security throughout  
✅ **86MB files** upload without timeouts  

**Your TUS implementation is production-ready!** 🚀