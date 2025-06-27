#!/usr/bin/env python3
"""
Test script for callback endpoint
"""
import asyncio
import sys
import json

# Add project root to path
sys.path.append('/Users/jaredjohnston/sermon_ai')

import httpx
from app.main import app

async def test_callback_endpoint():
    """Test the callback endpoint with various payloads"""
    print("🚀 CALLBACK ENDPOINT TEST")
    print("=" * 50)
    
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        
        # Test 1: GET test endpoint
        print("🔹 Testing GET /callback/test...")
        test_response = await client.get("/api/v1/transcription/callback/test")
        print(f"Status: {test_response.status_code}")
        print(f"Response: {test_response.json()}")
        
        # Test 2: Valid JSON callback
        print("\n🔹 Testing valid JSON callback...")
        valid_payload = {
            "request_id": "test-request-123",
            "results": {
                "channels": [
                    {
                        "alternatives": [
                            {
                                "transcript": "Hello world, this is a test transcript.",
                                "confidence": 0.95,
                                "utterances": [
                                    {
                                        "speaker": 0,
                                        "transcript": "Hello world, this is a test transcript.",
                                        "start": 0.0,
                                        "end": 3.5,
                                        "confidence": 0.95
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        json_response = await client.post(
            "/api/v1/transcription/callback",
            json=valid_payload
        )
        print(f"Status: {json_response.status_code}")
        print(f"Response: {json_response.json()}")
        
        # Test 3: Invalid JSON
        print("\n🔹 Testing invalid JSON...")
        try:
            invalid_response = await client.post(
                "/api/v1/transcription/callback",
                content="{ invalid json",
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {invalid_response.status_code}")
            print(f"Response: {invalid_response.text}")
        except Exception as e:
            print(f"Exception: {e}")
        
        # Test 4: Non-JSON content
        print("\n🔹 Testing non-JSON content...")
        text_response = await client.post(
            "/api/v1/transcription/callback",
            content="This is plain text",
            headers={"Content-Type": "text/plain"}
        )
        print(f"Status: {text_response.status_code}")
        print(f"Response: {text_response.json()}")
        
        # Test 5: Empty payload
        print("\n🔹 Testing empty payload...")
        empty_response = await client.post(
            "/api/v1/transcription/callback",
            json={}
        )
        print(f"Status: {empty_response.status_code}")
        print(f"Response: {empty_response.json()}")
        
        print("\n🎉 CALLBACK TESTS COMPLETED!")

if __name__ == "__main__":
    asyncio.run(test_callback_endpoint())