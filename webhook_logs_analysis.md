# Control Flow Analysis

## 🍽️ Restaurant Metaphor: "The Sermon Kitchen"

*Based on actual production logs from a 4GB video file processing*

### 🏪 **The Setup: "Marco's AI Transcription Restaurant"**

Imagine a sophisticated restaurant where raw sermon videos are transformed into perfectly organized, speaker-classified transcripts. Here's how your 4GB video file moved through our kitchen:

---

## 📋 **Act 1: Customer Arrival & Reservation (Lines 17-31)**
**"Welcome to Marco's! Let me prepare your table..."**

- **Customer arrives** (line 17): `mixed_sermon_video_4GB_1752831523965.mp4` walks in
- **Hostess checks ID** (lines 18-19): Validates user credentials and table assignment
- **Menu consultation** (lines 20-23): "I see you have a video file... we'll need our special video processing"
- **Reservation made** (lines 24-26): Creates a table reservation (media record: `9e215028-0d99-47ab-b692-59bb9b0683dc`)
- **Special accommodations** (lines 27-30): "This is a large order (3939MB), we'll use our premium TUS service"

---

## 🚚 **Act 2: Delivery Arrival (Lines 32-57)**
**"Your order has arrived! Let's get cooking..."**

- **Delivery truck arrives** (line 32): Upload completion webhook received
- **Security check** (line 33): Bouncer verifies the delivery is legitimate
- **Inventory inspection** (lines 34-46): "Hmm, 4GB video file, looks good!"
- **Kitchen assignment** (lines 47-56): "This goes to the video processing station"
- **Quick acknowledgment** (line 57): "Got it! We'll start cooking right away" (200 OK - fast acknowledge!)

---

## 👨‍🍳 **Act 3: Kitchen Prep Work (Lines 58-75)**
**"Let's extract the audio essence from this video..."**

- **Head chef takes over** (line 58): Video processing pipeline starts
- **Special equipment** (lines 59-62): Uses the professional FFmpeg audio extractor
- **The magic happens** (lines 63-71): 
  - Extracts 62.4MB of pure audio from 4GB video
  - Uploads to processing station in 13.6 seconds (4.6MB/s)
  - *"Beautiful! The audio is perfectly extracted!"*
- **Cleanup** (lines 72-75): Cleans up temporary files, preps for next step

---

## 📝 **Act 4: Order Ticket Creation (Lines 76-99)**
**"Time to send this to our transcription specialists..."**

- **Order ticket created** (line 77): Transcript record `e221ce0d-e70d-455a-8ada-a3a4a94280b3`
- **Specialist called** (lines 80-91): Deepgram transcription service summoned
- **Special instructions** (lines 81-89): "Make sure to separate speakers, add punctuation, use nova-3 model"
- **Handoff to specialists** (lines 91-97): "Request ID: `342a4509-5d48-43a7-8d71-4ba9c18093ad`"
- **Kitchen update** (lines 98-99): "Transcription order is out for processing!"

---

## 🔄 **Act 5: The Specialist Returns (Lines 100-124)**
**"Your transcription is ready! Now for the AI magic..."**

- **Specialist returns** (line 100): Deepgram callback with completed transcription
- **Quality check** (lines 101-116): "1,174,085 bytes of beautiful transcript data!"
- **Order fulfillment** (lines 117-121): Updates the order record with results
- **The modern twist** (lines 122-124): "Now let's add our AI speaker classification!" 
  - Queues background job for 486 utterances
  - **Fast service** (line 129): Customer gets their 200 OK immediately

---

## 🤖 **Act 6: The AI Sous Chef (Lines 126-137)**
**"Let me organize this by speaker for you..."**

- **AI sous chef starts** (line 126): Background worker `worker-0` takes the job
- **Mise en place** (lines 127-131): Gathers all ingredients (transcript data)
- **The secret sauce** (line 132): OpenAI GPT-4 analyzes all 486 utterances
- **Final plating** (lines 133-137): 
  - Identifies 4 different speakers: worship, sermon, announcements
  - Filters down to 3,555 words and 480 utterances
  - *"Perfection! The dish is ready to serve!"*

---

## 🎯 **The Magic of the Fast Acknowledge Pattern**

**Notice the beautiful timing in Act 5:**
- **Line 124**: AI job queued ✅
- **Line 129**: Customer gets 200 OK (Deepgram is happy!) ✅
- **Lines 126-137**: AI processing happens in background ✅

**This is like telling a restaurant customer:** *"Your order is confirmed and being prepared!"* instead of making them wait at the counter until the entire meal is cooked, plated, and garnished.

---

## 📊 **Restaurant Performance Metrics**

| Stage | Duration | Status | Notes |
|-------|----------|--------|-------|
| Preparation | ~1 second | ✅ | Quick table setup |
| Video Processing | ~14 seconds | ✅ | Audio extraction from 4GB video |
| Transcription | ~18 minutes | ✅ | Deepgram processing 62MB audio |
| AI Classification | ~4 seconds | ✅ | OpenAI analyzing 486 utterances |
| **Total** | **~18 minutes** | ✅ | **From raw video to classified transcript** |

---

## 🍽️ **The Final Dish**

Your customer receives a beautifully organized transcript with:
- **4 identified speakers** (worship, sermon, announcements)
- **3,555 filtered words** of pure content
- **480 utterances** perfectly classified
- **Zero webhook timeouts** thanks to fast acknowledge pattern

*"Bon appétit! Your sermon transcript is served!"* 🍽️

---

## Upload to Transcription Flow Logs
INFO:     Application startup complete.
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/auth/v1/signup "HTTP/2 200 OK"
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/auth/v1/token?grant_type=password "HTTP/2 200 OK"
INFO:httpx:HTTP Request: GET https://fapjxekuyckurahbtvrt.supabase.co/auth/v1/user "HTTP/2 200 OK"
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/user_profiles "HTTP/2 201 Created"
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/clients "HTTP/2 201 Created"
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/client_users "HTTP/2 201 Created"
INFO:     127.0.0.1:62522 - "POST /api/v1/auth/signup HTTP/1.1" 200 OK
INFO:     127.0.0.1:62585 - "GET /api/v1/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:62596 - "OPTIONS /api/v1/transcription/upload/prepare HTTP/1.1" 200 OK
INFO:httpx:HTTP Request: GET https://fapjxekuyckurahbtvrt.supabase.co/auth/v1/admin/users/b38c155c-d12a-4e4e-90e3-69b47288caf8 "HTTP/2 200 OK"
INFO:app.api.endpoints.transcription:Preparing upload for file: mixed_sermon_video_4GB_1752831523965.mp4 from user: jaredjohnston000+tokentest_20250718_103610@gmail.com
INFO:httpx:HTTP Request: GET https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/client_users?select=client_id&user_id=eq.b38c155c-d12a-4e4e-90e3-69b47288caf8&deleted_at=is.null "HTTP/2 200 OK"
INFO:httpx:HTTP Request: GET https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/clients?select=%2A&id=eq.7a5266f9-fb05-4f4b-8222-12b0cd5662df&deleted_at=is.null "HTTP/2 200 OK"
INFO:app.api.endpoints.transcription:Validating file: mixed_sermon_video_4GB_1752831523965.mp4 (4130612492 bytes)
INFO:app.services.file_type_service:Detected video file: video/mp4
INFO:app.services.file_type_service:Detected video file: video/mp4
INFO:app.api.endpoints.transcription:File category detected: video, Processing type: video_with_audio_extraction
INFO:app.api.endpoints.transcription:Creating media record for mixed_sermon_video_4GB_1752831523965.mp4
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/media "HTTP/2 201 Created"
INFO:app.api.endpoints.transcription:Media record created: 9e215028-0d99-47ab-b692-59bb9b0683dc
INFO:app.api.endpoints.transcription:Using TUS resumable upload for large file: 3939.26MB
INFO:app.api.endpoints.transcription:Upload URL generated: https://fapjxekuyckurahbtvrt.supabase.co/storage/v1/upload/resumable
INFO:app.api.endpoints.transcription:Upload method: tus_resumable
INFO:app.api.endpoints.transcription:Upload preparation successful for media 9e215028-0d99-47ab-b692-59bb9b0683dc using tus_resumable
INFO:     127.0.0.1:62596 - "POST /api/v1/transcription/upload/prepare HTTP/1.1" 200 OK
INFO:app.api.endpoints.transcription:🔔 Upload completion webhook received
INFO:app.api.endpoints.transcription:✅ Webhook authentication verified
INFO:app.api.endpoints.transcription:Webhook data: {
  "object_name": "clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/uploads/mixed_sermon_video_4GB_1752831523965.mp4",
  "bucket_name": "sermons",
  "metadata": {
    "eTag": "\"72df58b26c46c46b28529c4fb12d5108-657\"",
    "size": 4130612492,
    "mimetype": "video/mp4",
    "cacheControl": "max-age=3600",
    "lastModified": "2025-07-18T09:38:45.000Z",
    "contentLength": 4130612492,
    "httpStatusCode": 200
  }
}...
INFO:app.api.endpoints.transcription:📋 Processing Edge Function format
INFO:httpx:HTTP Request: GET https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/media?select=%2A&filename=eq.mixed_sermon_video_4GB_1752831523965.mp4&client_id=eq.7a5266f9-fb05-4f4b-8222-12b0cd5662df&deleted_at=is.null&order=created_at.desc "HTTP/2 200 OK"
INFO:app.api.endpoints.transcription:📋 Processing upload completion for video file
INFO:app.api.endpoints.transcription:   Media ID: 9e215028-0d99-47ab-b692-59bb9b0683dc
INFO:app.api.endpoints.transcription:   Client ID: 7a5266f9-fb05-4f4b-8222-12b0cd5662df
INFO:app.api.endpoints.transcription:   User ID: 00000000-0000-0000-0000-000000000000
INFO:app.api.endpoints.transcription:   Processing type: unknown
INFO:httpx:HTTP Request: PATCH https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/media?id=eq.9e215028-0d99-47ab-b692-59bb9b0683dc "HTTP/2 200 OK"
INFO:app.api.endpoints.transcription:✅ Updated media 9e215028-0d99-47ab-b692-59bb9b0683dc with webhook timestamp
INFO:app.api.endpoints.transcription:🎬 Starting video processing pipeline (background)
INFO:     2a05:d01c:76e:7901:967d:f906:68a4:2ae1:0 - "POST /api/v1/transcription/webhooks/upload-complete HTTP/1.1" 200 OK
INFO:app.api.endpoints.transcription:🎬 Starting video processing for media 9e215028-0d99-47ab-b692-59bb9b0683dc
INFO:app.services.audio_extraction_service:🎬 Extracting audio from stored video: clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/uploads/mixed_sermon_video_4GB_1752831523965.mp4
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/storage/v1/object/sign/sermons/clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/uploads/mixed_sermon_video_4GB_1752831523965.mp4 "HTTP/2 200 OK"
INFO:app.services.audio_extraction_service:🎵 Attempting streaming audio extraction...
INFO:app.services.audio_extraction_service:✅ Streaming extraction successful
INFO:app.services.audio_extraction_service:📤 Starting audio upload to processing bucket:
INFO:app.services.audio_extraction_service:   📁 File: audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3
INFO:app.services.audio_extraction_service:   📊 Size: 62.4MB
INFO:app.services.audio_extraction_service:   ⏱️ Estimated upload time: ~31 seconds
INFO:app.services.audio_extraction_service:   🎯 Destination: clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/storage/v1/object/sermon-processing/clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3 "HTTP/2 200 OK"
INFO:app.services.audio_extraction_service:✅ Audio upload completed!
INFO:app.services.audio_extraction_service:   ⏱️ Duration: 13.6s
INFO:app.services.audio_extraction_service:   🚀 Speed: 4.6MB/s
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/storage/v1/object/sign/sermon-processing/clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3 "HTTP/2 200 OK"
INFO:app.services.audio_extraction_service:✅ Audio extraction completed: clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3
INFO:app.services.audio_extraction_service:🧹 Cleaned up temp audio: /var/folders/qj/6xsx03_94kddbqwph6yj7g800000gn/T/sermon_ai_audio/temp_audio_9e215028-0d99-47ab-b692-59bb9b0683dc.mp3
INFO:app.api.endpoints.transcription:✅ Audio extracted to: clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts "HTTP/2 201 Created"
INFO:app.api.endpoints.transcription:✅ Created transcript record: e221ce0d-e70d-455a-8ada-a3a4a94280b3
INFO:httpx:HTTP Request: POST https://fapjxekuyckurahbtvrt.supabase.co/storage/v1/object/sign/sermon-processing/clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3 "HTTP/2 200 OK"
INFO:app.services.supabase_service:Generated signed URL for clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3 (expires in 3600s)
INFO:app.services.deepgram_service:Callback URL configured as: https://charmed-stud-modest.ngrok-free.app/api/v1/transcription/callback
INFO:app.services.deepgram_service:Transcription options: {
    "callback": "https://charmed-stud-modest.ngrok-free.app/api/v1/transcription/callback",
    "diarize": true,
    "model": "nova-3",
    "paragraphs": true,
    "punctuate": true,
    "smart_format": true,
    "utterances": true
}
INFO:app.services.deepgram_service:Signed URL: https://fapjxekuyckurahbtvrt.supabase.co/storage/v1/object/sign/sermon-processing/clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV81MmIwZWE4YS1mYTAxLTQ0MGItYjRiNC0wNDU2NWFhODQ2NGEiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJzZXJtb24tcHJvY2Vzc2luZy9jbGllbnRzLzdhNTI2NmY5LWZiMDUtNGY0Yi04MjIyLTEyYjBjZDU2NjJkZi9hdWRpby9hdWRpb185ZTIxNTAyOC0wZDk5LTQ3YWItYjY5Mi01OWJiOWIwNjgzZGNfNmQzNzhlNDkubXAzIiwiaWF0IjoxNzUyODMyNjEyLCJleHAiOjE3NTI4MzYyMTJ9.yjCuMDCbM-Vbvj_xM9xoEJ9QOk8_aWxZUHb1JcmWCOw
INFO:httpx:HTTP Request: POST https://api.deepgram.com/v1/listen?callback=https%3A%2F%2Fcharmed-stud-modest.ngrok-free.app%2Fapi%2Fv1%2Ftranscription%2Fcallback&diarize=true&model=nova-3&paragraphs=true&punctuate=true&smart_format=true&utterances=true "HTTP/1.1 200 OK"
INFO:app.services.deepgram_service:Deepgram API Response Details:
INFO:app.services.deepgram_service:Response type: <class 'deepgram.clients.listen.v1.rest.response.AsyncPrerecordedResponse'>
INFO:app.services.deepgram_service:Response raw: {
    "request_id": "342a4509-5d48-43a7-8d71-4ba9c18093ad"
}
INFO:app.api.endpoints.transcription:✅ Deepgram transcription started: 342a4509-5d48-43a7-8d71-4ba9c18093ad
INFO:httpx:HTTP Request: PATCH https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts?id=eq.e221ce0d-e70d-455a-8ada-a3a4a94280b3 "HTTP/2 200 OK"
INFO:app.api.endpoints.transcription:✅ Background video processing completed for media 9e215028-0d99-47ab-b692-59bb9b0683dc
INFO:app.api.endpoints.transcription:🔔 Deepgram callback received
INFO:app.api.endpoints.transcription:   Method: POST
INFO:app.api.endpoints.transcription:   URL: https://charmed-stud-modest.ngrok-free.app/api/v1/transcription/callback
INFO:app.api.endpoints.transcription:   Headers: {'host': 'charmed-stud-modest.ngrok-free.app', 'content-length': '1174085', 'accept': '*/*', 'content-type': 'application/json', 'dg-token': '5f73e36b-a37b-406c-b29c-bdcf2bc80c91', 'x-forwarded-for': '38.246.42.147', 'x-forwarded-host': 'charmed-stud-modest.ngrok-free.app', 'x-forwarded-proto': 'https', 'accept-encoding': 'gzip'}
INFO:app.api.endpoints.transcription:   Body size: 1174085 bytes
INFO:app.api.endpoints.transcription:   Content-Type: application/json
INFO:app.api.endpoints.transcription:✅ Successfully parsed JSON payload
INFO:app.api.endpoints.transcription:📋 Request ID: 342a4509-5d48-43a7-8d71-4ba9c18093ad
INFO:app.api.endpoints.transcription:🎯 Processing transcription results...
INFO:app.api.endpoints.transcription:
Channel 1 Transcript Details:
INFO:app.api.endpoints.transcription:
Alternative 1:
INFO:app.api.endpoints.transcription:Full Transcript: Every miracle we've seen, it's a glimpse of what is coming. So by faith, help us believe. Amen? And we know we will see.
**Remaining transcript content excluded for brevity**
ill I be fat in heaven? You know, I'm at the age where I've got furniture disease. Do you know furniture dis
... [TRUNCATED]
INFO:app.api.endpoints.transcription:💾 Updating transcript record for request_id: 342a4509-5d48-43a7-8d71-4ba9c18093ad
INFO:httpx:HTTP Request: GET https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts?select=%2A&request_id=eq.342a4509-5d48-43a7-8d71-4ba9c18093ad&deleted_at=is.null "HTTP/2 200 OK"
INFO:app.api.endpoints.transcription:✅ Found transcript record: e221ce0d-e70d-455a-8ada-a3a4a94280b3
INFO:httpx:HTTP Request: PATCH https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts?id=eq.e221ce0d-e70d-455a-8ada-a3a4a94280b3 "HTTP/2 200 OK"
INFO:app.api.endpoints.transcription:✅ Transcript updated successfully - Status: completed
INFO:app.api.endpoints.transcription:🎯 Queuing AI speaker classification for 486 utterances
INFO:app.services.background_job_service:Queued job ai_classification_1752832630307 of type ai_classification
INFO:app.api.endpoints.transcription:✅ AI classification job queued: ai_classification_1752832630307
INFO:app.api.endpoints.transcription:📅 Audio file scheduled for cleanup after 30 days: clients/7a5266f9-fb05-4f4b-8222-12b0cd5662df/audio/audio_9e215028-0d99-47ab-b692-59bb9b0683dc_6d378e49.mp3
INFO:app.services.background_job_service:Worker worker-0 processing job ai_classification_1752832630307
INFO:app.services.background_job_service:Processing AI classification for transcript e221ce0d-e70d-455a-8ada-a3a4a94280b3
INFO:httpx:HTTP Request: PATCH https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts?id=eq.e221ce0d-e70d-455a-8ada-a3a4a94280b3 "HTTP/2 200 OK"
INFO:     38.246.42.147:0 - "POST /api/v1/transcription/callback HTTP/1.1" 200 OK
INFO:httpx:HTTP Request: GET https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts?select=%2A&id=eq.e221ce0d-e70d-455a-8ada-a3a4a94280b3&deleted_at=is.null "HTTP/2 200 OK"
INFO:httpx:HTTP Request: PATCH https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts?id=eq.e221ce0d-e70d-455a-8ada-a3a4a94280b3 "HTTP/2 200 OK"
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: PATCH https://fapjxekuyckurahbtvrt.supabase.co/rest/v1/transcripts?id=eq.e221ce0d-e70d-455a-8ada-a3a4a94280b3 "HTTP/2 200 OK"
INFO:app.services.background_job_service:✅ AI classification completed for transcript e221ce0d-e70d-455a-8ada-a3a4a94280b3
INFO:app.services.background_job_service:📊 Speakers: [<SpeakerCategory.worship: 'worship'>, <SpeakerCategory.sermon: 'sermon'>, <SpeakerCategory.sermon: 'sermon'>, <SpeakerCategory.announcements: 'announcements'>]
INFO:app.services.background_job_service:📊 Filtered: 3555 words, 480 utterances
INFO:app.services.background_job_service:Job ai_classification_1752832630307 completed successfully by worker-0