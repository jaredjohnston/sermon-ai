#!/usr/bin/env python3
"""
Quick test to verify callback storage with correct ngrok URL
"""
import asyncio
import sys
import os

sys.path.append('/Users/jaredjohnston/sermon_ai')

import httpx
from app.main import app

async def test_callback_storage():
    print("🔥 QUICK CALLBACK STORAGE TEST")
    print("=" * 40)
    
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        
        # Create user and upload
        signup_data = {
            "email": f"callback_test_{int(asyncio.get_event_loop().time())}@example.com",
            "password": "TestPassword123!",
            "first_name": "Callback",
            "last_name": "Test",
            "country": "United States",
            "organization_name": "Callback Test Church"
        }
        
        signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
        auth_data = signup_response.json()
        access_token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print("✅ User created")
        
        # Upload test file
        with open("test_audio.mp4", "rb") as audio_file:
            files = {"file": ("callback_test.mp4", audio_file, "video/mp4")}
            upload_response = await client.post(
                "/api/v1/transcription/upload", 
                files=files,
                headers=headers
            )
            
        upload_data = upload_response.json()
        request_id = upload_data["request_id"]
        transcript_id = upload_data["transcript_id"]
        
        print(f"✅ Upload successful")
        print(f"   Request ID: {request_id}")
        print(f"   Transcript ID: {transcript_id}")
        print(f"   Callback URL: https://0141-87-75-198-220.ngrok-free.app/api/v1/transcription/callback")
        print(f"\n⏳ Waiting 45 seconds for Deepgram callback...")
        
        # Wait and check
        await asyncio.sleep(45)
        
        status_response = await client.get(f"/api/v1/transcription/status/{transcript_id}", headers=headers)
        status_data = status_response.json()
        print(f"\n📊 Final Status: {status_data['status']}")
        
        if status_data['status'] == 'completed':
            content_response = await client.get(f"/api/v1/transcription/{transcript_id}", headers=headers)
            content_data = content_response.json()
            
            if content_data['content']:
                transcript_text = content_data['content'].get('full_transcript', '')
                print(f"🎉 SUCCESS! Transcript stored:")
                print(f"   Length: {len(transcript_text)} characters")
                print(f"   Preview: {transcript_text[:100]}...")
                return True
            else:
                print("❌ Completed but no content")
                return False
        else:
            print(f"⏳ Still {status_data['status']}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_callback_storage())
    print(f"\n{'✅ SUCCESS' if result else '❓ INCOMPLETE'}")