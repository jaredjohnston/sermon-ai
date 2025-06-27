#!/usr/bin/env python3
"""
Test script to verify transcript storage from Deepgram callbacks
Run from project root: python test_transcript_storage.py
"""
import asyncio
import sys
import os
import json
from uuid import uuid4

# Add project root to path
sys.path.append('/Users/jaredjohnston/sermon_ai')

import httpx
from app.main import app
from app.services.supabase_service import supabase_service

async def test_transcript_storage():
    """Test if Deepgram results are properly stored in Supabase"""
    print("🔍 TRANSCRIPT STORAGE TEST")
    print("=" * 50)
    
    # Use httpx with test client
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        
        # Step 1: Create a user and upload a file to get a real transcript record
        print("🔹 Creating test user and uploading file...")
        signup_data = {
            "email": f"storage_test_{int(asyncio.get_event_loop().time())}@example.com",
            "password": "TestPassword123!",
            "first_name": "Storage",
            "last_name": "Test",
            "country": "United States",
            "organization_name": "Storage Test Church"
        }
        
        signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
        if signup_response.status_code != 200:
            print(f"❌ Signup failed: {signup_response.text}")
            return False
            
        auth_data = signup_response.json()
        access_token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ User created successfully")
        
        # Upload a test file
        test_audio_path = "test_audio.mp4"
        if not os.path.exists(test_audio_path):
            print(f"❌ Test audio file not found: {test_audio_path}")
            return False
            
        with open(test_audio_path, "rb") as audio_file:
            files = {"file": ("storage_test.mp4", audio_file, "video/mp4")}
            upload_response = await client.post(
                "/api/v1/transcription/upload", 
                files=files,
                headers=headers
            )
            
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.text}")
            return False
            
        upload_data = upload_response.json()
        request_id = upload_data["request_id"]
        transcript_id = upload_data["transcript_id"]
        print(f"✅ Upload successful - Request ID: {request_id}")
        print(f"   Transcript ID: {transcript_id}")
        
        # Step 2: Check initial transcript status (should be "processing")
        print(f"\n🔹 Checking initial transcript status...")
        status_response = await client.get(f"/api/v1/transcription/status/{transcript_id}", headers=headers)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"📋 Initial Status: {status_data['status']}")
            print(f"   Request ID: {status_data.get('request_id')}")
        else:
            print(f"❌ Failed to get status: {status_response.text}")
            
        # Step 3: Wait for Deepgram callback and check periodically
        print(f"\n🔹 Waiting for Deepgram callback...")
        print("   (This may take 30-60 seconds for real transcription)")
        
        max_attempts = 12  # Wait up to 2 minutes
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            await asyncio.sleep(10)  # Wait 10 seconds between checks
            
            print(f"   Attempt {attempt}/{max_attempts}: Checking transcript status...")
            
            # Check status via API
            status_response = await client.get(f"/api/v1/transcription/status/{transcript_id}", headers=headers)
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data['status']
                print(f"   Status: {current_status}")
                
                if current_status in ['completed', 'failed']:
                    print(f"\n🎯 Transcription finished with status: {current_status}")
                    
                    # Get full transcript content
                    content_response = await client.get(f"/api/v1/transcription/{transcript_id}", headers=headers)
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        
                        print(f"📊 TRANSCRIPT STORAGE RESULTS:")
                        print(f"   Status: {content_data['status']}")
                        print(f"   Has Content: {content_data['content'] is not None}")
                        
                        if content_data['content']:
                            content = content_data['content']
                            print(f"   Full Transcript Length: {len(content.get('full_transcript', ''))}")
                            print(f"   Utterances Count: {len(content.get('utterances', []))}")
                            print(f"   Confidence: {content.get('confidence', 'N/A')}")
                            
                            # Show first part of transcript
                            full_text = content.get('full_transcript', '')
                            if full_text:
                                preview = full_text[:200] + "..." if len(full_text) > 200 else full_text
                                print(f"\n📝 Transcript Preview:")
                                print(f"   \"{preview}\"")
                                
                                print(f"\n✅ SUCCESS: Deepgram results are being stored in Supabase!")
                                return True
                            else:
                                print(f"\n⚠️  Transcript completed but no content found")
                                return False
                        else:
                            print(f"\n⚠️  Transcript {current_status} but no content available")
                            if current_status == 'failed':
                                print(f"   Error: {status_data.get('error_message', 'Unknown error')}")
                            return False
                    else:
                        print(f"❌ Failed to get transcript content: {content_response.text}")
                        return False
            else:
                print(f"   ❌ Failed to check status: {status_response.text}")
                
        print(f"\n⏰ Timeout: Transcript still processing after {max_attempts * 10} seconds")
        print("   This might be normal for longer audio files or Deepgram delays")
        return False

if __name__ == "__main__":
    print("🧪 SermonAI Transcript Storage Test")
    print("Testing if Deepgram results are stored in Supabase...")
    
    success = asyncio.run(test_transcript_storage())
    
    if success:
        print(f"\n🎉 STORAGE TEST PASSED!")
        print("   Deepgram callbacks are properly updating transcript records")
        exit(0)
    else:
        print(f"\n❓ STORAGE TEST INCONCLUSIVE")
        print("   Check logs for more details")
        exit(1)