import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse
import pytest
from unittest.mock import call
from app.services.deepgram_service import deepgram_service
from io import BytesIO
from app.services.deepgram_service import DeepgramService

@pytest.fixture
def mock_supabase_client(mocker):
    mock_client = mocker.Mock()
    mock_storage = mocker.Mock()
    mock_client.storage.from_.return_value = mock_storage
    mock_storage.upload.return_value = {"Key": "test_file.mp4"}
    mock_storage.get_public_url.return_value = "https://supabase.com/storage/test_file.mp4"
    return mock_client

@pytest.fixture
def test_file():
    # Create a small test file in memory
    return BytesIO(b"test content")

@pytest.mark.asyncio
async def test_supabase_upload(mock_supabase_client, test_file):
    """Test uploading a file to Supabase storage"""
    # Create service instance with mocked client
    service = DeepgramService()
    service.supabase = mock_supabase_client
    
    # Test the upload
    file_url = await service.upload_to_supabase(test_file)
    
    # Get the mock storage object
    mock_storage = mock_supabase_client.storage.from_.return_value
    
    # Verify from_ was called twice with 'videos-test'
    assert mock_supabase_client.storage.from_.call_count == 2
    mock_supabase_client.storage.from_.assert_has_calls([
        call('videos-test'),
        call('videos-test')
    ], any_order=True)
    
    # Verify upload was called once
    assert mock_storage.upload.call_count == 1
    
    # Verify get_public_url was called once
    assert mock_storage.get_public_url.call_count == 1
    
    # Verify the returned URL
    assert file_url == "https://supabase.com/storage/test_file.mp4"

if __name__ == "__main__":
    asyncio.run(test_supabase_upload()) 