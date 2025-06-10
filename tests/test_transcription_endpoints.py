"""
Tests for the transcription API endpoints (/api/v1/transcription/*)
This test suite verifies:
1. File upload endpoint (/upload)
2. Callback endpoint (/callback)
3. Error handling (invalid files, size limits)
4. Full transcription flow
"""

import asyncio
import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.deepgram_service import deepgram_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create test client
client = TestClient(app)

def test_upload_endpoint_success():
    """Test successful file upload and transcription via the API endpoint"""
    # Prepare the test file
    with open("test_audio.mp4", "rb") as file:
        files = {"file": ("test_audio.mp4", file, "video/mp4")}
        response = client.post("/api/v1/transcription/upload", files=files)
        
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "callback_url" in data
    assert "status" in data
    assert data["status"] == "processing"

def test_upload_endpoint_invalid_type():
    """Test file upload with invalid content type"""
    # Create a text file
    with open("test.txt", "w") as f:
        f.write("This is not an audio file")
    
    # Try to upload it
    with open("test.txt", "rb") as file:
        files = {"file": ("test.txt", file, "text/plain")}
        response = client.post("/api/v1/transcription/upload", files=files)
    
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]

def test_callback_endpoint():
    """Test the callback endpoint with sample Deepgram data"""
    sample_callback_data = {
        "request_id": "test_request_id",
        "results": {
            "channels": [{
                "alternatives": [{
                    "transcript": "This is a test transcript.",
                    "confidence": 0.95,
                    "utterances": [{
                        "speaker": 0,
                        "start": 0.0,
                        "end": 3.0,
                        "transcript": "This is a test transcript.",
                        "confidence": 0.95
                    }]
                }]
            }]
        }
    }
    
    response = client.post("/api/v1/transcription/callback", json=sample_callback_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "processed_at" in data

@pytest.mark.asyncio
async def test_full_transcription_flow():
    """Test the complete transcription flow from upload to callback"""
    try:
        # 1. Upload file through API endpoint
        with open("test_audio.mp4", "rb") as file:
            logger.info("Starting full transcription flow test...")
            files = {"file": ("test_audio.mp4", file, "video/mp4")}
            response = client.post("/api/v1/transcription/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            request_id = data["request_id"]
            logger.info(f"Upload successful! Request ID: {request_id}")
            
            # 2. Simulate callback from Deepgram
            callback_data = {
                "request_id": request_id,
                "results": {
                    "channels": [{
                        "alternatives": [{
                            "transcript": "This is the transcribed content.",
                            "confidence": 0.98,
                            "utterances": [{
                                "speaker": 0,
                                "start": 0.0,
                                "end": 3.0,
                                "transcript": "This is the transcribed content.",
                                "confidence": 0.98
                            }]
                        }]
                    }]
                }
            }
            
            callback_response = client.post("/api/v1/transcription/callback", json=callback_data)
            assert callback_response.status_code == 200
            logger.info("Callback processed successfully!")
            
    except Exception as e:
        logger.error(f"Test failed!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        raise

if __name__ == "__main__":
    print("\nℹ️  Make sure your FastAPI app is running!")
    print("   Start the app: uvicorn app.main:app --reload")
    
    # Run the async test
    asyncio.run(test_full_transcription_flow()) 