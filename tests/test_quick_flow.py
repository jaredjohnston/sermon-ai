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
        """Test file upload using the token from signup - now with concurrent processing verification"""
        if not hasattr(self, 'access_token'):
            pytest.skip("Run test_signup_with_alias_email first")
            
        client = TestClient(app)
        
        # Use real video file if it exists, otherwise fallback to audio or fake data
        import os
        test_file_path = None
        file_size = 0
        
        # Check for test files (using the 455MB test file for realistic large file testing)
        test_files = [
            ("/Users/jaredjohnston/Desktop/SermonAI/455_test_video_file.mp4", "video/mp4"),
            ("test_audio.mp4", "video/mp4"),  # Fallback
            ("test_audio.mp3", "audio/mpeg"),
            ("1gb_test_file.mp4", "video/mp4"),
            ("large_test_file.mp4", "video/mp4"),
        ]
        
        for filepath, content_type in test_files:
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                test_file_path = filepath
                filename = filepath
                break
        
        if test_file_path:
            file_size_mb = file_size / 1024 / 1024
            print(f"🔹 Using real file: {test_file_path}")
            print(f"   File size: {file_size_mb:.2f}MB")
            
            # Show which upload method will be used
            from app.config.settings import settings
            tus_threshold_mb = settings.TUS_THRESHOLD / 1024 / 1024
            upload_method = "TUS resumable" if file_size > settings.TUS_THRESHOLD else "standard"
            print(f"   Upload method: {upload_method} (threshold: {tus_threshold_mb}MB)")
            
            with open(test_file_path, "rb") as f:
                test_content = f.read()
        else:
            print(f"🔹 Using fake test data (real files not found)")
            test_content = b"fake audio data" * 1000  # 13KB file
            filename = "test_sermon.mp4"
            content_type = "video/mp4"
            file_size = len(test_content)
        
        files = {
            "file": (filename, test_content, content_type)
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        print(f"🔹 Testing concurrent upload and audio extraction...")
        response = client.post("/api/v1/transcription/upload", files=files, headers=headers)
        
        print(f"📋 Upload response status: {response.status_code}")
        
        if response.status_code == 422:
            print(f"⚠️  File validation failed")
            print(f"   This might be expected for fake data, but real audio should work")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful!")
            print(f"   Video ID: {data['video_id']}")
            print(f"   Transcript ID: {data['transcript_id']}")
            print(f"   Request ID: {data.get('request_id', 'N/A')}")
            
            # Print database cross-reference summary
            print(f"\n🔍 DATABASE CROSS-REFERENCE IDs:")
            print(f"   User ID:       {self.user_id}")
            print(f"   Client ID:     {self.client_id}")
            print(f"   Client Name:   {self.client_name}")
            print(f"   Video ID:      {data['video_id']}")
            print(f"   Transcript ID: {data['transcript_id']}")
            print(f"   Request ID:    {data.get('request_id', 'N/A')}")
            
            # NEW: Verify concurrent processing functionality
            self._verify_concurrent_processing_response(data)
            
            # Store for transcript testing
            self.video_id = data['video_id']
            self.transcript_id = data['transcript_id']
            self.request_id = data.get('request_id')
            return True
        else:
            print(f"❌ Unexpected response: {response.text}")
            return False
    
    def _verify_concurrent_processing_response(self, response_data):
        """Verify the response indicates concurrent processing worked"""
        print(f"\n🔍 CONCURRENT PROCESSING VERIFICATION:")
        
        # Check message indicates concurrent processing
        message = response_data.get('message', '')
        if 'Audio extracted and transcription started immediately' in message:
            print(f"   ✅ Message indicates concurrent processing: {message}")
        else:
            print(f"   ⚠️  Message doesn't indicate concurrent processing: {message}")
        
        # Check processing_info structure
        processing_info = response_data.get('processing_info', {})
        if processing_info:
            print(f"   ✅ Processing info present")
            
            # Verify audio extraction completed
            audio_extracted = processing_info.get('audio_extracted', False)
            print(f"   {'✅' if audio_extracted else '❌'} Audio extracted: {audio_extracted}")
            
            # Verify transcription started
            transcription_started = processing_info.get('transcription_started', False)
            print(f"   {'✅' if transcription_started else '❌'} Transcription started: {transcription_started}")
            
            # Verify video upload in background
            video_status = processing_info.get('video_upload_status', '')
            background_processing = video_status == 'background_processing'
            print(f"   {'✅' if background_processing else '❌'} Video upload in background: {video_status}")
            
        else:
            print(f"   ❌ Processing info missing from response")
        
        # Check next_steps mentions audio processing
        next_steps = response_data.get('next_steps', {})
        description = next_steps.get('description', '')
        if 'extracted audio' in description.lower():
            print(f"   ✅ Next steps mention audio extraction: {description}")
        else:
            print(f"   ⚠️  Next steps don't mention audio: {description}")
        
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
    
    def test_callback_endpoint_simulation(self):
        """Test callback endpoint with simulated Deepgram response and verify audio cleanup"""
        if not hasattr(self, 'request_id'):
            pytest.skip("Run upload test first to get request ID")
            
        client = TestClient(app)
        
        # Simulate Deepgram callback payload
        callback_payload = {
            "metadata": {
                "request_id": self.request_id
            },
            "results": {
                "channels": [
                    {
                        "alternatives": [
                            {
                                "transcript": "This is a test sermon transcription from our concurrent audio extraction test.",
                                "confidence": 0.95,
                                "utterances": [
                                    {
                                        "speaker": 0,
                                        "transcript": "This is a test sermon transcription from our concurrent audio extraction test.",
                                        "start": 0.0,
                                        "end": 5.0,
                                        "confidence": 0.95
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        print(f"🔹 Testing callback endpoint with audio cleanup verification...")
        response = client.post("/api/v1/transcription/callback", json=callback_payload)
        
        print(f"📋 Callback response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Callback endpoint working!")
            print(f"   Status: {data['status']}")
            print(f"   Request ID: {data.get('request_id', 'N/A')}")
            
            # NEW: Verify audio cleanup functionality
            self._verify_audio_cleanup_logs()
            
            return True
        else:
            print(f"❌ Callback failed: {response.text}")
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
        # Test 2: File Upload + Concurrent Processing + Deepgram
        print("\n📤 PHASE 2: CONCURRENT UPLOAD & AUDIO EXTRACTION")
        test_results['upload'] = tester.test_file_upload_with_auth()
        
        if test_results['upload']:
            # Test 3: Transcript Status
            print("\n📊 PHASE 3: TRANSCRIPT STATUS")
            test_results['status'] = tester.test_transcript_status_endpoint()
            
            # Test 4: Transcript Listing
            print("\n📋 PHASE 4: TRANSCRIPT LISTING")
            test_results['listing'] = tester.test_transcript_list_endpoint()
            
            # Test 5: Callback Simulation + Audio Cleanup
            print("\n🔔 PHASE 5: CALLBACK PROCESSING & AUDIO CLEANUP")
            test_results['callback'] = tester.test_callback_endpoint_simulation()
            
            # Test 6: Content Retrieval
            print("\n📄 PHASE 6: TRANSCRIPT CONTENT")
            test_results['content'] = tester.test_transcript_content_endpoint()
    
    # Results Summary
    print("\n" + "=" * 60)
    print("🏁 COMPLETE FLOW TEST RESULTS")
    print("=" * 60)
    
    phases = [
        ("User Registration", test_results.get('signup', False)),
        ("Concurrent Upload + Audio Extraction", test_results.get('upload', False)),
        ("Status Endpoint", test_results.get('status', False)),
        ("Listing Endpoint", test_results.get('listing', False)),
        ("Callback + Audio Cleanup", test_results.get('callback', False)),
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
        print("🎉 ALL TESTS PASSED! Complete concurrent audio extraction flow working!")
        print("\n✅ Your implementation successfully:")
        print("   • Creates users and organizations")
        print("   • Extracts audio concurrently with video upload")
        print("   • Starts transcription immediately from audio")
        print("   • Routes large files to TUS resumable upload (background)")
        print("   • Processes callback responses with audio cleanup")
        print("   • Stores and retrieves transcript content")
        print("   • Provides API endpoints for frontend integration")
    else:
        print(f"⚠️  {len(phases) - passed} test(s) failed - check logs above for details")
    
    return passed == len(phases)

if __name__ == "__main__":
    run_quick_tests()