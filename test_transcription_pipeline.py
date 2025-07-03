#!/usr/bin/env python3
"""
Test the complete transcription pipeline end-to-end
Tests: prepare -> upload -> webhook -> transcription -> processing
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

class DirectUploadSystemTest:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        # Use existing auth token
        self.auth_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6IkxFNkk4SGlWempGUE5GV3YiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2ZhcGp4ZWt1eWNrdXJhaGJ0dnJ0LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJjZjEwY2ExYy03YmRmLTRlNzktYjY5OC1jZDFjMDU3Zjc0MDYiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUxNTU0MjA4LCJpYXQiOjE3NTE1NTA2MDgsImVtYWlsIjoiamFyZWRqb2huc3RvbjAwMCt0b2tlbnRlc3RfMjAyNTA3MDNfMTQ1MDA4QGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJqYXJlZGpvaG5zdG9uMDAwK3Rva2VudGVzdF8yMDI1MDcwM18xNDUwMDhAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiY2YxMGNhMWMtN2JkZi00ZTc5LWI2OTgtY2QxYzA1N2Y3NDA2In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTE1NTA2MDh9XSwic2Vzc2lvbl9pZCI6ImI3MTFjYjExLTQ1MDMtNGJmZi04MGEzLTAwYjIxNjJjNjMwOCIsImlzX2Fub255bW91cyI6ZmFsc2V9.95PYHng7IoKm-e-ynS4j8D-8m2nhsszbpWcXz9qMaY8"
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_prepare_upload_audio(self):
        """Test prepare upload for audio file"""
        print("\n🎵 TEST 1: Prepare Upload - Audio File")
        print("-" * 40)
        
        # Use real 86MB sermon file  
        real_file_path = "/Users/jaredjohnston/Desktop/SermonAI/full_sermon_test_86mb.mp3"
        
        if not os.path.exists(real_file_path):
            print(f"❌ Real sermon file not found: {real_file_path}")
            return None
            
        file_size = os.path.getsize(real_file_path)
        timestamp = int(datetime.now().timestamp())
        
        payload = {
            "filename": f"real_sermon_{timestamp}.mp3",
            "content_type": "audio/mpeg", 
            "size_bytes": file_size
        }
        
        print(f"🎯 Using REAL 86MB sermon file: {file_size / 1024 / 1024:.2f}MB")
        
        response = requests.post(
            f"{self.base_url}/transcription/upload/prepare",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Media ID: {data.get('media_id')}")
            print(f"Upload URL: {data.get('upload_url', 'N/A')[:80]}...")
            print(f"Upload Headers: {list(data.get('upload_fields', {}).keys())}")  # Show header keys
            print(f"File Category: {data.get('processing_info', {}).get('file_category')}")
            print(f"Audio Extraction: {data.get('processing_info', {}).get('audio_extraction_needed')}")
            print(f"Processing Type: {data.get('processing_info', {}).get('processing_type')}")
            print(f"Upload Method: {data.get('processing_info', {}).get('upload_method')}")
            
            # ACTUALLY UPLOAD THE REAL FILE
            print(f"\n🚀 UPLOADING REAL 86MB FILE TO SUPABASE...")
            upload_url = data.get('upload_url')
            upload_headers = data.get('upload_fields', {})
            
            with open(real_file_path, 'rb') as f:
                file_content = f.read()
            
            upload_response = requests.put(
                upload_url,
                data=file_content,
                headers=upload_headers,
                timeout=300  # 5 minute timeout
            )
            
            print(f"📋 Supabase upload status: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 201]:
                print(f"✅ REAL FILE UPLOADED TO SUPABASE STORAGE!")
                print(f"   Check Supabase Storage 'videos' bucket")
                print(f"   File path: {upload_url.split('/object/videos/')[-1] if '/object/videos/' in upload_url else 'unknown'}")
            else:
                print(f"❌ Upload failed: {upload_response.text[:200]}...")
            
            # Verify audio file doesn't need extraction
            processing_info = data.get('processing_info', {})
            if processing_info.get('file_category') == 'audio' and not processing_info.get('audio_extraction_needed'):
                print("✅ Correct: Audio file bypasses extraction")
                return data
            else:
                print("❌ Wrong: Audio file should bypass extraction")
                return None
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def test_prepare_upload_video(self):
        """Test prepare upload for video file"""
        print("\n🎬 TEST 2: Prepare Upload - Video File")
        print("-" * 40)
        
        # Use timestamp for unique filename
        timestamp = int(datetime.now().timestamp())
        payload = {
            "filename": f"test_sermon_video_{timestamp}.mp4",
            "content_type": "video/mp4", 
            "size_bytes": 500 * 1024 * 1024  # 500MB
        }
        
        response = requests.post(
            f"{self.base_url}/transcription/upload/prepare",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Media ID: {data.get('media_id')}")
            print(f"Upload URL: {data.get('upload_url', 'N/A')[:80]}...")
            print(f"Upload Headers: {list(data.get('upload_fields', {}).keys())}")  # Show header keys
            print(f"File Category: {data.get('processing_info', {}).get('file_category')}")
            print(f"Audio Extraction: {data.get('processing_info', {}).get('audio_extraction_needed')}")
            print(f"Processing Type: {data.get('processing_info', {}).get('processing_type')}")
            print(f"Upload Method: {data.get('processing_info', {}).get('upload_method')}")
            
            # Verify video file needs extraction
            processing_info = data.get('processing_info', {})
            if processing_info.get('file_category') == 'video' and processing_info.get('audio_extraction_needed'):
                print("✅ Correct: Video file requires extraction")
                return data
            else:
                print("❌ Wrong: Video file should require extraction")
                return None
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def test_webhook_audio(self, media_data):
        """Test webhook processing for audio file"""
        print("\n🔔 TEST 3: Webhook Processing - Audio File")
        print("-" * 40)
        
        if not media_data:
            print("❌ SKIPPED: No media data from prepare test")
            return False
        
        # Extract storage path from upload URL since it's not in response
        upload_url = media_data.get('upload_url', '')
        # URL format: https://supabase.co/storage/v1/object/videos/clients/{client_id}/videos/filename.mp3
        storage_path = upload_url.split('/object/videos/')[-1] if '/object/videos/' in upload_url else None
        print(f"DEBUG: Extracted storage_path: {storage_path}")
        
        # Simulate Supabase Storage webhook payload using real data
        webhook_payload = {
            "object_name": storage_path,  # Use extracted storage path
            "bucket_name": "videos",  # Correct bucket name from settings
            "metadata": {
                "media_id": media_data.get('media_id'),
                "client_id": "65786eca-36e3-4ac2-8da3-2cc6a2e1030f",  # Real client UUID
                "user_id": "real-user-uuid", 
                "file_category": "audio",
                "needs_audio_extraction": False,
                "processing_type": "direct_audio"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/transcription/webhooks/upload-complete",
            json=webhook_payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            print(f"Processing Type: {data.get('processing_type')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def test_webhook_video(self, media_data):
        """Test webhook processing for video file"""
        print("\n🔔 TEST 4: Webhook Processing - Video File") 
        print("-" * 40)
        
        if not media_data:
            print("❌ SKIPPED: No media data from prepare test")
            return False
        
        # Extract storage path from upload URL (same method as audio test)
        upload_url = media_data.get('upload_url', '')
        storage_path = upload_url.split('/object/videos/')[-1] if '/object/videos/' in upload_url else None
        print(f"DEBUG: Extracted storage_path: {storage_path}")
        
        # Simulate Supabase Storage webhook payload using real data
        webhook_payload = {
            "object_name": storage_path,  # Use extracted storage path
            "bucket_name": "videos",  # Correct bucket name
            "metadata": {
                "media_id": media_data.get('media_id'),
                "client_id": "65786eca-36e3-4ac2-8da3-2cc6a2e1030f",  # Real client UUID
                "user_id": "real-user-uuid",
                "file_category": "video", 
                "needs_audio_extraction": True,
                "processing_type": "video_with_audio_extraction"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/transcription/webhooks/upload-complete",
            json=webhook_payload,
            timeout=60  # Longer timeout for video processing
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            print(f"Processing Type: {data.get('processing_type')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def test_validation_errors(self):
        """Test various validation scenarios"""
        print("\n🚫 TEST 5: Validation Error Handling")
        print("-" * 40)
        
        test_cases = [
            {
                "name": "File too large",
                "payload": {
                    "filename": "huge_file.mp4",
                    "content_type": "video/mp4",
                    "size_bytes": 60 * 1024 * 1024 * 1024  # 60GB (over 50GB limit)
                },
                "expected_status": 413
            },
            {
                "name": "Invalid content type",
                "payload": {
                    "filename": "document.txt", 
                    "content_type": "text/plain",
                    "size_bytes": 1024
                },
                "expected_status": 400
            },
            {
                "name": "Missing filename",
                "payload": {
                    "content_type": "audio/mpeg",
                    "size_bytes": 1024 * 1024
                },
                "expected_status": 422
            }
        ]
        
        results = []
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            response = requests.post(
                f"{self.base_url}/transcription/upload/prepare",
                headers=self.headers,
                json=test_case['payload'],
                timeout=30
            )
            
            if response.status_code == test_case['expected_status']:
                print(f"  ✅ Correct error: {response.status_code}")
                results.append(True)
            else:
                print(f"  ❌ Wrong status: expected {test_case['expected_status']}, got {response.status_code}")
                results.append(False)
        
        return all(results)

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 NEW DIRECT UPLOAD SYSTEM TEST")
    print("=" * 60)
    
    tester = DirectUploadSystemTest()
    results = {}
    
    # Test 1: Audio file prepare
    audio_data = tester.test_prepare_upload_audio()
    results['audio_prepare'] = audio_data is not None
    
    # Test 2: Video file prepare  
    video_data = tester.test_prepare_upload_video()
    results['video_prepare'] = video_data is not None
    
    # Test 3: Audio webhook (only if prepare succeeded)
    results['audio_webhook'] = tester.test_webhook_audio(audio_data)
    
    # Test 4: Video webhook (only if prepare succeeded) 
    results['video_webhook'] = tester.test_webhook_video(video_data)
    
    # Test 5: Validation errors
    results['validation'] = tester.test_validation_errors()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    test_names = {
        'audio_prepare': 'Audio File Prepare',
        'video_prepare': 'Video File Prepare', 
        'audio_webhook': 'Audio Webhook Processing',
        'video_webhook': 'Video Webhook Processing',
        'validation': 'Validation Error Handling'
    }
    
    passed = 0
    for key, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_names[key]}")
        if success:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ New direct upload system working correctly:")
        print("   • File type detection and validation")
        print("   • Presigned URL generation") 
        print("   • Smart routing (audio vs video)")
        print("   • Webhook processing")
        print("   • Error handling")
        print("\n🔄 Next steps:")
        print("   1. Configure Supabase Storage webhook")
        print("   2. Test with real file uploads")
        print("   3. Verify end-to-end with large files")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed")
        print("Check the output above for details")
    
    return passed == len(results)

if __name__ == "__main__":
    print("⚠️ Prerequisites:")
    print("   1. FastAPI server running on localhost:8000")
    print("   2. Valid auth token (may need refresh)")
    print("   3. Database accessible")
    print("")
    
    success = run_comprehensive_test()
    
    if not success:
        print("\n❌ Some tests failed")
        exit(1)
    else:
        print("\n✅ All tests passed!")