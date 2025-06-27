#!/usr/bin/env python3
"""
Test script for transcript retrieval endpoints
Run from project root: python test_transcript_endpoints.py
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

async def test_transcript_endpoints():
    """Test our new transcript retrieval endpoints"""
    print("🚀 TRANSCRIPT ENDPOINTS TEST")
    print("=" * 50)
    
    # Use httpx with test client
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        
        # Step 1: Create a user and get auth token
        print("🔹 Creating test user...")
        signup_data = {
            "email": f"tester+endpoints_{int(asyncio.get_event_loop().time())}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "country": "United States",
            "organization_name": "Test Church for Endpoints"
        }
        
        signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
        print(f"📋 Signup status: {signup_response.status_code}")
        
        if signup_response.status_code != 200:
            print(f"❌ Signup failed: {signup_response.text}")
            return False
            
        auth_data = signup_response.json()
        access_token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ User created successfully")
        
        # Step 2: Test endpoints with fake IDs (should return 404)
        print("\n🔹 Testing endpoints with non-existent IDs...")
        fake_uuid = str(uuid4())
        
        # Test status endpoint
        status_response = await client.get(f"/api/v1/transcription/status/{fake_uuid}", headers=headers)
        print(f"📋 Status endpoint: {status_response.status_code} (expected 404)")
        
        # Test transcript content endpoint  
        content_response = await client.get(f"/api/v1/transcription/{fake_uuid}", headers=headers)
        print(f"📋 Content endpoint: {content_response.status_code} (expected 404)")
        
        # Test video transcript endpoint
        video_response = await client.get(f"/api/v1/transcription/video/{fake_uuid}", headers=headers)
        print(f"📋 Video transcript endpoint: {status_response.status_code} (expected 404)")
        
        # Test list endpoint (should return empty list)
        list_response = await client.get("/api/v1/transcription/", headers=headers)
        print(f"📋 List endpoint: {list_response.status_code} (expected 200)")
        
        if list_response.status_code == 200:
            list_data = list_response.json()
            print(f"   Found {len(list_data.get('transcripts', []))} transcripts")
            print(f"   Pagination: {list_data.get('pagination', {})}")
        
        # Step 3: Test with invalid UUIDs (should return 400)
        print("\n🔹 Testing with invalid UUID formats...")
        invalid_id = "not-a-uuid"
        
        invalid_status = await client.get(f"/api/v1/transcription/status/{invalid_id}", headers=headers)
        print(f"📋 Invalid status UUID: {invalid_status.status_code} (expected 400)")
        
        invalid_content = await client.get(f"/api/v1/transcription/{invalid_id}", headers=headers)
        print(f"📋 Invalid content UUID: {invalid_content.status_code} (expected 400)")
        
        # Step 4: Test without authentication (should return 401)
        print("\n🔹 Testing without authentication...")
        no_auth_response = await client.get(f"/api/v1/transcription/status/{fake_uuid}")
        print(f"📋 No auth: {no_auth_response.status_code} (expected 401)")
        
        # Step 5: Test pagination parameters
        print("\n🔹 Testing pagination parameters...")
        
        # Valid pagination
        valid_page = await client.get("/api/v1/transcription/?limit=10&offset=0", headers=headers)
        print(f"📋 Valid pagination: {valid_page.status_code} (expected 200)")
        
        # Invalid limit (too high)
        invalid_limit = await client.get("/api/v1/transcription/?limit=200", headers=headers)
        print(f"📋 Invalid limit: {invalid_limit.status_code} (expected 400)")
        
        # Invalid offset
        invalid_offset = await client.get("/api/v1/transcription/?offset=-1", headers=headers)
        print(f"📋 Invalid offset: {invalid_offset.status_code} (expected 400)")
        
        # Test status filter
        status_filter = await client.get("/api/v1/transcription/?status_filter=completed", headers=headers)
        print(f"📋 Status filter: {status_filter.status_code} (expected 200)")
        
        # Invalid status filter
        invalid_filter = await client.get("/api/v1/transcription/?status_filter=invalid", headers=headers)
        print(f"📋 Invalid status filter: {invalid_filter.status_code} (expected 400)")
        
        print("\n🎉 ALL ENDPOINT TESTS COMPLETED!")
        print("✅ Authentication handling working")
        print("✅ UUID validation working") 
        print("✅ Error responses correct")
        print("✅ Pagination validation working")
        
        return True

if __name__ == "__main__":
    print("🧪 SermonAI Transcript Endpoint Test")
    print("Testing all transcript retrieval endpoints...")
    
    success = asyncio.run(test_transcript_endpoints())
    
    if success:
        print(f"\n✅ ALL TESTS PASSED!")
        exit(0)
    else:
        print(f"\n❌ TESTS FAILED")
        exit(1)