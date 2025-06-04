import asyncio
import os
from pathlib import Path
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import create_application
from app.config.settings import settings

# Initialize test client
app = create_application()
client = TestClient(app)

# Test file configurations
TEST_FILES = {
    'small': {
        'size': '10MB',
        'path': 'tests/data/small_video.mp4',
        'expected_duration': 60  # 1 minute
    },
    'medium': {
        'size': '500MB',
        'path': 'tests/data/medium_video.mp4',
        'expected_duration': 1800  # 30 minutes
    },
    'large': {
        'size': '2GB',
        'path': 'tests/data/large_video.mp4',
        'expected_duration': 7200  # 2 hours
    }
}

def test_file_upload_validation():
    """Test file validation before upload"""
    # Test invalid file type
    with open('tests/data/invalid.txt', 'rb') as f:
        response = client.post(
            "/api/v1/transcription/upload",
            files={"file": ("invalid.txt", f, "text/plain")}
        )
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]

    # Test file too large (mock a 5GB file)
    large_file_path = Path('tests/data/large_file.mp4')
    try:
        # Create a sparse file of 5GB
        large_file_path.touch()
        large_file_path.write_bytes(b'\0' * (5 * 1024 * 1024 * 1024))  # 5GB of zeros
        
        with open(large_file_path, 'rb') as f:
            response = client.post(
                "/api/v1/transcription/upload",
                files={"file": ("large_file.mp4", f, "video/mp4")}
            )
            assert response.status_code == 400
            assert "exceeds maximum allowed size" in response.json()["detail"]
    finally:
        if large_file_path.exists():
            large_file_path.unlink()

async def test_transcription_flow():
    """Test the entire transcription flow with different file sizes"""
    # Create a temporary callback server to receive Deepgram responses
    callback_received = asyncio.Event()
    callback_data = {}
    
    async def mock_callback_server():
        async def handle_callback(request):
            data = await request.json()
            callback_data['results'] = data
            callback_received.set()
            return {'status': 'success'}
        
        # Start a simple HTTP server for callbacks
        async with httpx.AsyncClient() as client:
            while not callback_received.is_set():
                await asyncio.sleep(1)
    
    # Start mock callback server
    callback_task = asyncio.create_task(mock_callback_server())
    
    try:
        # Test with actual video file
        test_file_path = Path(TEST_FILES['small']['path'])
        if not test_file_path.exists():
            pytest.skip(f"Test file {test_file_path} not found")
        
        with open(test_file_path, 'rb') as f:
            response = client.post(
                "/api/v1/transcription/upload",
                files={"file": ("test_video.mp4", f, "video/mp4")}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "request_id" in result
            
            # Wait for callback (with timeout)
            try:
                await asyncio.wait_for(callback_received.wait(), timeout=300)  # 5 minutes timeout
                assert 'results' in callback_data
                assert 'utterances' in callback_data['results']
            except asyncio.TimeoutError:
                pytest.fail("Callback not received within timeout")
    
    finally:
        callback_task.cancel()
        try:
            await callback_task
        except asyncio.CancelledError:
            pass

def test_concurrent_uploads():
    """Test handling of concurrent file uploads"""
    import concurrent.futures
    import time
    
    def upload_file(file_path):
        with open(file_path, 'rb') as f:
            response = client.post(
                "/api/v1/transcription/upload",
                files={"file": (os.path.basename(file_path), f, "video/mp4")}
            )
            return response.status_code, response.json()
    
    # Test with 3 concurrent uploads
    test_file_path = Path(TEST_FILES['small']['path'])
    if not test_file_path.exists():
        pytest.skip(f"Test file {test_file_path} not found")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(upload_file, str(test_file_path))
            for _ in range(3)
        ]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            status_code, response_data = future.result()
            results.append((status_code, response_data))
        
        # Verify all uploads were accepted
        assert all(status_code == 200 for status_code, _ in results)
        # Verify each got a unique request_id
        request_ids = [data["request_id"] for _, data in results]
        assert len(set(request_ids)) == len(request_ids)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 