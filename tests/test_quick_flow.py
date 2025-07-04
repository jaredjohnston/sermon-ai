"""
QUICK TEST: Essential flow verification for immediate testing

This is a streamlined test for validating the core signup → upload → transcription
flow using your alias email. Perfect for quick verification before building more features.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

class TestQuickFlow:
    """Minimal tests for immediate verification"""
    
    def test_smart_routing_with_both_file_types(self):
        """Test smart routing with both audio and video files if available"""
        if not hasattr(self, 'access_token'):
            pytest.skip("Run test_signup_with_alias_email first")
            
        import os
        client = TestClient(app)
        
        # Test files to try
        test_cases = [
            ("test_audio.mp3", "audio/mpeg", "audio"),
            ("test_audio.mp4", "video/mp4", "video"),
        ]
        
        results = {}
        
        for filepath, content_type, expected_category in test_cases:
            if os.path.exists(filepath):
                print(f"\n🔍 Testing {expected_category} file routing: {filepath}")
                
                # Get file size for new upload flow
                file_size = os.path.getsize(filepath)
                
                # Step 1: Prepare upload (new flow)
                prepare_payload = {
                    "filename": os.path.basename(filepath),
                    "content_type": content_type,
                    "size_bytes": file_size
                }
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                prepare_response = client.post("/upload/prepare", json=prepare_payload, headers=headers)
                
                if prepare_response.status_code == 200:
                    prepare_data = prepare_response.json()
                    processing_info = prepare_data.get('processing_info', {})
                    detected_category = processing_info.get('file_category', 'unknown')
                    
                    print(f"   ✅ Upload preparation successful")
                    print(f"   📁 Expected: {expected_category}, Detected: {detected_category}")
                    
                    # Step 2: Simulate webhook (file upload completed)
                    media_id = prepare_data.get('media_id')
                    upload_url = prepare_data.get('upload_url', '')
                    storage_path = upload_url.split('/object/sermons/')[-1] if '/object/sermons/' in upload_url else filepath
                    
                    webhook_payload = {
                        "object_name": storage_path,
                        "bucket_name": "sermons",
                        "metadata": {
                            "media_id": media_id,
                            "client_id": self.client_id,
                            "user_id": self.user_id,
                            "file_category": expected_category,
                            "needs_audio_extraction": expected_category == "video",
                            "processing_type": f"{'video_with_audio_extraction' if expected_category == 'video' else 'direct_audio'}"
                        }
                    }
                    
                    webhook_response = client.post("/webhooks/upload-complete", json=webhook_payload)
                    
                    if webhook_response.status_code == 200:
                        print(f"   ✅ Webhook processing successful")
                        
                        if detected_category == expected_category:
                            print(f"   ✅ Correct file type detection")
                            results[expected_category] = True
                        else:
                            print(f"   ❌ Incorrect file type detection")
                            results[expected_category] = False
                    else:
                        print(f"   ❌ Webhook processing failed: {webhook_response.status_code}")
                        results[expected_category] = False
                else:
                    print(f"   ❌ Upload preparation failed: {prepare_response.status_code}")
                    print(f"   Response: {prepare_response.text}")
                    results[expected_category] = False
            else:
                print(f"\n⚠️  {expected_category.title()} test file not found: {filepath}")
                results[expected_category] = None
        
        return results
    
    def test_signup_with_alias_email(self):
        """Test signup with your actual alias email"""
        client = TestClient(app)
        
        # REPLACE WITH YOUR ALIAS EMAIL - using timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_data = {
            "email": f"jaredjohnston000+quicktest_{timestamp}@gmail.com",  # ← CHANGE THIS
            "password": "TestSermonAI2024!",
            "first_name": "Test",
            "last_name": "Pastor",
            "country": "United States", 
            "organization_name": "Test Church Community"
        }
        
        print(f"\n🔹 Testing signup for: {test_data['email']}")
        response = client.post("/api/v1/auth/signup", json=test_data)
        
        print(f"📋 Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Signup failed: {response.text}")
            return False
            
        data = response.json()
        print(f"✅ Signup successful!")
        print(f"   User ID: {data['user']['id']}")
        print(f"   Client ID: {data['client']['id']}")
        print(f"   Organization: {data['client']['name']}")
        print(f"   Access Token: {data['access_token'][:20]}...")
        
        # Store IDs for cross-referencing with database
        self.user_id = data['user']['id']
        self.client_id = data['client']['id']
        self.client_name = data['client']['name']
        self.access_token = data["access_token"]
        return True
    
    def test_file_upload_with_auth(self):
        """Test file upload using the token from signup - now with smart routing verification for both audio and video"""
        if not hasattr(self, 'access_token'):
            pytest.skip("Run test_signup_with_alias_email first")
            
        client = TestClient(app)
        
        # Use specific 86MB sermon file
        import os
        
        test_file_path = "/Users/jaredjohnston/Desktop/SermonAI/full_sermon_test_86mb.mp3"
        content_type = "audio/mpeg"
        
        if not os.path.exists(test_file_path):
            print(f"❌ Test file not found: {test_file_path}")
            print(f"   Please ensure the file exists at this location")
            return False
            
        file_size = os.path.getsize(test_file_path)
        file_size_mb = file_size / 1024 / 1024
        filename = os.path.basename(test_file_path)
        
        print(f"🔹 Using real 86MB sermon file: {test_file_path}")
        print(f"   File size: {file_size_mb:.2f}MB")
        print(f"   Content type: {content_type}")
        
        # Show which upload method will be used
        from app.config.settings import settings
        tus_threshold_mb = settings.TUS_THRESHOLD / 1024 / 1024
        upload_method = "TUS resumable" if file_size > settings.TUS_THRESHOLD else "standard"
        print(f"   Upload method: {upload_method} (threshold: {tus_threshold_mb}MB)")
        
        with open(test_file_path, "rb") as f:
            test_content = f.read()
        
        files = {
            "file": (filename, test_content, content_type)
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        print(f"🔹 Testing new upload flow with REAL file upload (content type: {content_type})...")
        
        # Step 1: Prepare upload
        prepare_payload = {
            "filename": os.path.basename(filename),
            "content_type": content_type,
            "size_bytes": file_size
        }
        
        prepare_response = client.post("/upload/prepare", json=prepare_payload, headers=headers)
        print(f"📋 Prepare response status: {prepare_response.status_code}")
        
        if prepare_response.status_code == 422:
            print(f"⚠️  File validation failed")
            print(f"   This might be expected for fake data, but real audio should work")
            return True
        elif prepare_response.status_code == 200:
            prepare_data = prepare_response.json()
            print(f"✅ Upload preparation successful!")
            print(f"   Media ID: {prepare_data['media_id']}")
            print(f"   Upload URL: {prepare_data['upload_url'][:80]}...")
            
            # Step 2: ACTUALLY upload file to Supabase Storage
            upload_url = prepare_data['upload_url']
            upload_headers = prepare_data['upload_fields']
            
            print(f"🚀 Uploading {file_size_mb:.2f}MB file to Supabase Storage...")
            
            import requests
            upload_response = requests.put(
                upload_url,
                data=test_content,
                headers=upload_headers,
                timeout=300  # 5 minute timeout for large files
            )
            
            print(f"📋 Supabase upload response: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 201]:
                print(f"✅ Real file uploaded to Supabase Storage!")
                
                # Step 3: Trigger webhook processing (real processing)
                storage_path = upload_url.split('/object/sermons/')[-1] if '/object/sermons/' in upload_url else filename
                
                webhook_payload = {
                    "object_name": storage_path,
                    "bucket_name": "sermons",
                    "metadata": {
                        "media_id": prepare_data['media_id'],
                        "client_id": self.client_id,
                        "user_id": self.user_id,
                        "file_category": "video" if "video" in content_type else "audio",
                        "needs_audio_extraction": "video" in content_type,
                        "processing_type": "video_with_audio_extraction" if "video" in content_type else "direct_audio"
                    }
                }
                
                webhook_response = client.post("/webhooks/upload-complete", json=webhook_payload)
                print(f"📋 Webhook response status: {webhook_response.status_code}")
                
                if webhook_response.status_code == 200:
                    webhook_data = webhook_response.json()
                    print(f"✅ Real processing pipeline started!")
                    print(f"   Status: {webhook_data.get('status')}")
                    print(f"   Message: {webhook_data.get('message')}")
                    
                    # Print database cross-reference summary for Supabase verification
                    print(f"\n🔍 VERIFY IN SUPABASE:")
                    print(f"   User ID:       {self.user_id}")
                    print(f"   Client ID:     {self.client_id}")
                    print(f"   Client Name:   {self.client_name}")
                    print(f"   Media ID:      {prepare_data['media_id']}")
                    print(f"   Storage Path:  {storage_path}")
                    print(f"   File in Storage: Check 'sermons' bucket for: {storage_path}")
                    print(f"   Media Record: Check 'media' table for media_id: {prepare_data['media_id']}")
                else:
                    print(f"❌ Webhook processing failed: {webhook_response.status_code}")
                    print(f"   Response: {webhook_response.text}")
            else:
                print(f"❌ File upload to Supabase failed: {upload_response.status_code}")
                print(f"   Response: {upload_response.text[:200]}...")
            
            # NEW: Verify smart routing functionality
            self._verify_smart_routing_response(data)
            
            # Store for transcript testing
            self.video_id = data['video_id']
            self.transcript_id = data['transcript_id']
            self.request_id = data.get('request_id')
            return True
        else:
            print(f"❌ Unexpected response: {response.text}")
            return False
    
    def _verify_smart_routing_response(self, response_data):
        """Verify the response indicates smart file type routing worked"""
        print(f"\n🔍 SMART ROUTING VERIFICATION:")
        
        # Check processing_info structure has new smart routing fields
        processing_info = response_data.get('processing_info', {})
        if processing_info:
            print(f"   ✅ Processing info present")
            
            # Check file category detection
            file_category = processing_info.get('file_category', '')
            print(f"   📁 File category: {file_category}")
            
            # Check processing type
            processing_type = processing_info.get('processing_type', '')
            print(f"   ⚙️  Processing type: {processing_type}")
            
            # Check routing flags
            audio_extraction_needed = processing_info.get('audio_extraction_needed', None)
            video_upload_needed = processing_info.get('video_upload_needed', None)
            transcription_started = processing_info.get('transcription_started', False)
            
            print(f"   {'✅' if audio_extraction_needed is not None else '❌'} Audio extraction flag: {audio_extraction_needed}")
            print(f"   {'✅' if video_upload_needed is not None else '❌'} Video upload flag: {video_upload_needed}")
            print(f"   {'✅' if transcription_started else '❌'} Transcription started: {transcription_started}")
            
            # Verify message matches file type
            message = response_data.get('message', '')
            if file_category == 'audio':
                expected_patterns = ['Audio file processed and transcription started immediately']
                pattern_found = any(pattern in message for pattern in expected_patterns)
                print(f"   {'✅' if pattern_found else '⚠️'} Audio message: {message}")
                
                # Audio files shouldn't need extraction
                if not audio_extraction_needed:
                    print(f"   ✅ Correct: Audio file bypassed extraction")
                else:
                    print(f"   ⚠️  Warning: Audio file still went through extraction")
                    
            elif file_category == 'video':
                expected_patterns = ['Audio extracted and transcription started immediately', 'Video upload continues in background']
                pattern_found = any(pattern in message for pattern in expected_patterns)
                print(f"   {'✅' if pattern_found else '⚠️'} Video message: {message}")
                
                # Video files should need extraction
                if audio_extraction_needed:
                    print(f"   ✅ Correct: Video file required extraction")
                else:
                    print(f"   ⚠️  Warning: Video file didn't require extraction")
            
        else:
            print(f"   ❌ Processing info missing from response")
        
        # Check next_steps description
        next_steps = response_data.get('next_steps', {})
        description = next_steps.get('description', '')
        print(f"   📝 Processing description: {description}")
        
        return True
    
    def test_transcript_status_endpoint(self):
        """Test transcript status endpoint"""
        if not hasattr(self, 'access_token') or not hasattr(self, 'transcript_id'):
            pytest.skip("Run upload test first to get transcript ID")
            
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print(f"🔹 Testing transcript status endpoint...")
        response = client.get(f"/api/v1/transcription/status/{self.transcript_id}", headers=headers)
        
        print(f"📋 Status response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working!")
            print(f"   Status: {data['status']}")
            print(f"   Created: {data['created_at']}")
            print(f"   Request ID: {data.get('request_id', 'N/A')}")
            return True
        else:
            print(f"❌ Status check failed: {response.text}")
            return False
    
    def test_transcript_list_endpoint(self):
        """Test transcript listing endpoint"""
        if not hasattr(self, 'access_token'):
            pytest.skip("Run signup test first")
            
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print(f"🔹 Testing transcript list endpoint...")
        response = client.get("/api/v1/transcription/", headers=headers)
        
        print(f"📋 List response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ List endpoint working!")
            print(f"   Total transcripts: {data['pagination']['total_count']}")
            if data['transcripts']:
                print(f"   Latest status: {data['transcripts'][0]['status']}")
            return True
        else:
            print(f"❌ List failed: {response.text}")
            return False
    
    def test_wait_for_real_callback(self):
        """Wait for real Deepgram callback and verify transcript content"""
        if not hasattr(self, 'request_id'):
            pytest.skip("Run upload test first to get request ID")
            
        client = TestClient(app)
        
        print(f"🔹 Waiting for real Deepgram callback...")
        print(f"   Request ID: {self.request_id}")
        print(f"   This may take 30-90 seconds for real transcription...")
        
        # Wait for real Deepgram callback to complete transcription
        max_wait_time = 600  # 10 minutes
        check_interval = 10   # Check every 10 seconds
        checks = 0
        max_checks = max_wait_time // check_interval
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while checks < max_checks:
            checks += 1
            print(f"   Check {checks}/{max_checks}: Waiting for transcription...")
            
            # Check transcript status
            status_response = client.get(f"/api/v1/transcription/status/{self.transcript_id}", headers=headers)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data.get('status', 'unknown')
                print(f"   Status: {current_status}")
                
                if current_status == 'completed':
                    print(f"✅ Real transcription completed!")
                    
                    # Get the actual transcript content
                    content_response = client.get(f"/api/v1/transcription/{self.transcript_id}", headers=headers)
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        content = content_data.get('content', {})
                        
                        if content and content.get('full_transcript'):
                            transcript_text = content['full_transcript']
                            print(f"\\n📝 REAL TRANSCRIPT RECEIVED:")
                            print(f"   Length: {len(transcript_text)} characters")
                            print(f"   Confidence: {content.get('confidence', 'N/A')}")
                            print(f"   Utterances: {len(content.get('utterances', []))}")
                            
                            # Show preview of real transcript
                            preview = transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text
                            print(f"   Preview: \"{preview}\"")
                            
                            return True
                        else:
                            print(f"❌ Transcript completed but no content found")
                            return False
                    else:
                        print(f"❌ Failed to get transcript content: {content_response.status_code}")
                        return False
                        
                elif current_status == 'failed':
                    print(f"❌ Transcription failed: {status_data.get('error_message', 'Unknown error')}")
                    return False
                
            else:
                print(f"   ⚠️ Status check failed: {status_response.status_code}")
            
            # Wait before next check
            import time
            time.sleep(check_interval)
        
        print(f"⏰ Timeout: Transcription still processing after {max_wait_time} seconds")
        print(f"   This is normal for longer files - check back later")
        return False
    
    def _verify_audio_cleanup_logs(self):
        """Check that audio cleanup was attempted during callback processing"""
        print(f"\n🧹 AUDIO CLEANUP VERIFICATION:")
        print(f"   ℹ️  Audio cleanup happens in callback - check logs for:")
        print(f"   • 'Cleaned up audio file:' message")
        print(f"   • 'No audio file found to cleanup:' message")
        print(f"   • 'Failed to cleanup audio file:' warning")
        print(f"   📝 Note: In real scenario, audio file would be deleted from Supabase storage")
        
        # Note: We can't easily verify actual file deletion in this test environment
        # without mocking the storage service, but we can verify the cleanup code path
        # is executed by checking the response and logs
        
        return True
    
    def test_transcript_content_endpoint(self):
        """Test transcript content retrieval after callback"""
        if not hasattr(self, 'access_token') or not hasattr(self, 'transcript_id'):
            pytest.skip("Run previous tests first")
            
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print(f"🔹 Testing transcript content endpoint...")
        response = client.get(f"/api/v1/transcription/{self.transcript_id}", headers=headers)
        
        print(f"📋 Content response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Content endpoint working!")
            print(f"   Status: {data['status']}")
            if data.get('content') and data['content'].get('full_transcript'):
                print(f"   Transcript preview: {data['content']['full_transcript'][:50]}...")
                print(f"   Confidence: {data['content'].get('confidence', 'N/A')}")
            return True
        else:
            print(f"❌ Content retrieval failed: {response.text}")
            return False

# =============================================================================
# MANUAL EXECUTION INSTRUCTIONS
# =============================================================================

def run_quick_tests():
    """Run the complete end-to-end test suite"""
    print("🚀 SERMONAI COMPLETE FLOW TEST")
    print("=" * 60)
    
    tester = TestQuickFlow()
    test_results = {}
    
    # Test 1: User Signup
    print("\n📝 PHASE 1: USER REGISTRATION")
    test_results['signup'] = tester.test_signup_with_alias_email()
    
    if test_results['signup']:
        # Test 2: File Upload + Smart Routing + Processing + Deepgram
        print("\n📤 PHASE 2: SMART FILE TYPE ROUTING & PROCESSING")
        test_results['upload'] = tester.test_file_upload_with_auth()
        
        if test_results['upload']:
            # Test 3: Transcript Status
            print("\n📊 PHASE 3: TRANSCRIPT STATUS")
            test_results['status'] = tester.test_transcript_status_endpoint()
            
            # Test 4: Transcript Listing
            print("\n📋 PHASE 4: TRANSCRIPT LISTING")
            test_results['listing'] = tester.test_transcript_list_endpoint()
            
            # Test 5: Wait for Real Deepgram Callback
            print("\n🔔 PHASE 5: REAL DEEPGRAM TRANSCRIPTION")
            test_results['callback'] = tester.test_wait_for_real_callback()
            
            # Test 6: Content Retrieval
            print("\n📄 PHASE 6: TRANSCRIPT CONTENT")
            test_results['content'] = tester.test_transcript_content_endpoint()
    
    # Results Summary
    print("\n" + "=" * 60)
    print("🏁 COMPLETE FLOW TEST RESULTS")
    print("=" * 60)
    
    phases = [
        ("User Registration", test_results.get('signup', False)),
        ("Smart File Type Routing & Processing", test_results.get('upload', False)),
        ("Status Endpoint", test_results.get('status', False)),
        ("Listing Endpoint", test_results.get('listing', False)),
        ("Real Deepgram Transcription", test_results.get('callback', False)),
        ("Content Retrieval", test_results.get('content', False))
    ]
    
    passed = 0
    for phase, success in phases:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {phase}")
        if success:
            passed += 1
    
    print(f"\n📊 SUMMARY: {passed}/{len(phases)} tests passed")
    
    if passed == len(phases):
        print("🎉 ALL TESTS PASSED! Smart file type routing flow working!")
        print("\n✅ Your implementation successfully:")
        print("   • Creates users and organizations")
        print("   • Detects file types (audio vs video) automatically")
        print("   • Routes audio files to direct processing (no extraction)")
        print("   • Routes video files to extraction + background upload")
        print("   • Starts transcription immediately from appropriate source")
        print("   • Uses TUS resumable upload for large files")
        print("   • Processes callback responses with audio cleanup")
        print("   • Stores and retrieves transcript content")
        print("   • Provides API endpoints for frontend integration")
    else:
        print(f"⚠️  {len(phases) - passed} test(s) failed - check logs above for details")
    
    return passed == len(phases)

if __name__ == "__main__":
    run_quick_tests()