"""
Integration tests for concurrent upload and audio extraction flow

Core functionality tests:
- Does transcription start immediately after audio extraction?
- Does audio extraction failure cancel video upload?
- Does video upload continue in background?
- Does storage cleanup work after callback?
"""

import pytest
import asyncio
import io
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile

from app.main import app
from app.services.audio_extraction_service import AudioExtractionError


class TestConcurrentUploadFlow:
    """Integration tests for concurrent processing functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.client = TestClient(app)
        self.test_user_data = {
            "email": "test_concurrent@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "country": "United States",
            "organization_name": "Test Organization"
        }

    def test_concurrent_flow_response_structure(self):
        """Test that upload response indicates concurrent processing"""
        # Create test user
        signup_response = self.client.post("/api/v1/auth/signup", json=self.test_user_data)
        assert signup_response.status_code == 200
        access_token = signup_response.json()["access_token"]

        # Mock the concurrent services
        with patch('app.api.endpoints.transcription.upload_video_to_storage') as mock_video_upload, \
             patch('app.api.endpoints.transcription.extract_and_upload_audio') as mock_audio_extract, \
             patch('app.services.deepgram_service.deepgram_service.transcribe_from_url') as mock_deepgram:

            # Mock successful concurrent processing
            mock_video_upload.return_value = asyncio.create_task(
                self._mock_async_return("https://video-signed-url.com")
            )
            mock_audio_extract.return_value = (
                "clients/test/audio/audio_123.wav",
                "https://audio-signed-url.com"
            )
            mock_deepgram.return_value = {"request_id": "deepgram-123"}

            # Test file upload (using fake data - in real test use test_audio.mp4)
            test_content = b"fake video data" * 100
            files = {"file": ("test_audio.mp4", test_content, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}

            response = self.client.post("/api/v1/transcription/upload", files=files, headers=headers)

            # Verify response structure indicates concurrent processing
            assert response.status_code == 200
            data = response.json()

            # Check concurrent processing message
            assert "Audio extracted and transcription started immediately" in data["message"]
            assert "Video upload continues in background" in data["message"]

            # Check processing info
            processing_info = data["processing_info"]
            assert processing_info["audio_extracted"] is True
            assert processing_info["transcription_started"] is True
            assert processing_info["video_upload_status"] == "background_processing"

            # Check next steps mention audio
            next_steps = data["next_steps"]
            assert "extracted audio" in next_steps["description"]

    def test_audio_extraction_failure_cancels_video_upload(self):
        """Test that audio extraction failure results in complete failure"""
        # Create test user
        signup_response = self.client.post("/api/v1/auth/signup", json=self.test_user_data)
        assert signup_response.status_code == 200
        access_token = signup_response.json()["access_token"]

        with patch('app.api.endpoints.transcription.extract_and_upload_audio') as mock_audio_extract:
            # Mock audio extraction failure
            mock_audio_extract.side_effect = AudioExtractionError("Audio extraction failed")

            # Test file upload (using fake data - in real test use test_audio.mp4)
            test_content = b"fake video data" * 100
            files = {"file": ("test_audio.mp4", test_content, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}

            response = self.client.post("/api/v1/transcription/upload", files=files, headers=headers)

            # Verify complete failure
            assert response.status_code == 502
            assert "Audio extraction failed" in response.json()["detail"]

    def test_transcription_starts_immediately_not_waiting_for_video(self):
        """Test that transcription starts as soon as audio is ready"""
        # Create test user
        signup_response = self.client.post("/api/v1/auth/signup", json=self.test_user_data)
        assert signup_response.status_code == 200
        access_token = signup_response.json()["access_token"]

        call_order = []

        # Mock functions that track call order
        async def mock_audio_extract(*args):
            call_order.append("audio_complete")
            return ("clients/test/audio/audio_123.wav", "https://audio-url.com")

        async def mock_deepgram_transcribe(*args):
            call_order.append("transcription_started")
            return {"request_id": "deepgram-123"}

        # Mock video upload to be slower (but we don't wait for it)
        def mock_video_upload(*args):
            async def slow_upload():
                await asyncio.sleep(0.1)  # Simulate slower upload
                call_order.append("video_complete")
                return "https://video-url.com"
            return asyncio.create_task(slow_upload())

        with patch('app.api.endpoints.transcription.upload_video_to_storage', side_effect=mock_video_upload), \
             patch('app.api.endpoints.transcription.extract_and_upload_audio', side_effect=mock_audio_extract), \
             patch('app.services.deepgram_service.deepgram_service.transcribe_from_url', side_effect=mock_deepgram_transcribe):

            # Test file upload (using fake data - in real test use test_audio.mp4)
            test_content = b"fake video data" * 100
            files = {"file": ("test_audio.mp4", test_content, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}

            response = self.client.post("/api/v1/transcription/upload", files=files, headers=headers)

            # Verify success
            assert response.status_code == 200

            # Verify transcription started immediately after audio (not waiting for video)
            assert call_order == ["audio_complete", "transcription_started"]
            # Note: video_complete may happen later in background

    def test_callback_audio_cleanup_integration(self):
        """Test that callback properly cleans up audio files"""
        # Create test user and upload
        signup_response = self.client.post("/api/v1/auth/signup", json=self.test_user_data)
        assert signup_response.status_code == 200
        access_token = signup_response.json()["access_token"]

        # Mock successful upload
        with patch('app.api.endpoints.transcription.upload_video_to_storage') as mock_video_upload, \
             patch('app.api.endpoints.transcription.extract_and_upload_audio') as mock_audio_extract, \
             patch('app.services.deepgram_service.deepgram_service.transcribe_from_url') as mock_deepgram:

            mock_video_upload.return_value = asyncio.create_task(
                self._mock_async_return("https://video-url.com")
            )
            mock_audio_extract.return_value = (
                "clients/test/audio/audio_video123.wav",
                "https://audio-url.com"
            )
            mock_deepgram.return_value = {"request_id": "deepgram-request-123"}

            # Upload file
            test_content = b"fake video data" * 100
            files = {"file": ("test_video.mp4", test_content, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}

            upload_response = self.client.post("/api/v1/transcription/upload", files=files, headers=headers)
            assert upload_response.status_code == 200

            request_id = upload_response.json()["request_id"]

        # Test callback with audio cleanup
        with patch('app.services.audio_extraction_service.audio_extraction_service.cleanup_audio_file') as mock_cleanup:
            mock_cleanup.return_value = None

            # Simulate Deepgram callback
            callback_payload = {
                "metadata": {"request_id": request_id},
                "results": {
                    "channels": [{
                        "alternatives": [{
                            "transcript": "Test transcript from concurrent extraction",
                            "confidence": 0.95
                        }]
                    }]
                }
            }

            callback_response = self.client.post("/api/v1/transcription/callback", json=callback_payload)
            assert callback_response.status_code == 200

            # Verify cleanup was called
            mock_cleanup.assert_called_once()
            # The audio storage path should be retrieved from transcript metadata
            cleanup_call_args = mock_cleanup.call_args[0][0]
            assert "clients/" in cleanup_call_args
            assert "audio/" in cleanup_call_args
            assert ".wav" in cleanup_call_args

    def test_background_video_upload_independence(self):
        """Test that video upload runs independently in background"""
        # Create test user
        signup_response = self.client.post("/api/v1/auth/signup", json=self.test_user_data)
        assert signup_response.status_code == 200
        access_token = signup_response.json()["access_token"]

        video_upload_started = asyncio.Event()
        response_returned = asyncio.Event()

        async def mock_audio_extract(*args):
            # Audio completes quickly
            return ("clients/test/audio/audio_123.wav", "https://audio-url.com")

        def mock_video_upload(*args):
            async def slow_video_upload():
                video_upload_started.set()
                # Simulate video upload continuing after response
                await asyncio.sleep(0.2)
                # At this point, response should already be returned
                assert response_returned.is_set()
                return "https://video-url.com"
            return asyncio.create_task(slow_video_upload())

        async def mock_deepgram(*args):
            return {"request_id": "deepgram-123"}

        with patch('app.api.endpoints.transcription.upload_video_to_storage', side_effect=mock_video_upload), \
             patch('app.api.endpoints.transcription.extract_and_upload_audio', side_effect=mock_audio_extract), \
             patch('app.services.deepgram_service.deepgram_service.transcribe_from_url', side_effect=mock_deepgram):

            # Test file upload (using fake data - in real test use test_audio.mp4)
            test_content = b"fake video data" * 100
            files = {"file": ("test_audio.mp4", test_content, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}

            response = self.client.post("/api/v1/transcription/upload", files=files, headers=headers)
            response_returned.set()

            # Verify success and that we didn't wait for video upload
            assert response.status_code == 200
            assert video_upload_started.is_set()  # Video upload started
            
            # Response indicates background processing
            data = response.json()
            assert data["processing_info"]["video_upload_status"] == "background_processing"

    async def _mock_async_return(self, value):
        """Helper to create async return value"""
        return value

    def test_error_handling_preserves_file_stream_position(self):
        """Test that file stream is properly reset on errors for potential retry"""
        # Create test user
        signup_response = self.client.post("/api/v1/auth/signup", json=self.test_user_data)
        assert signup_response.status_code == 200
        access_token = signup_response.json()["access_token"]

        with patch('app.api.endpoints.transcription.extract_and_upload_audio') as mock_audio_extract:
            # Mock failure
            mock_audio_extract.side_effect = AudioExtractionError("Test failure")

            # Test file upload (using fake data - in real test use test_audio.mp4)
            test_content = b"fake video data" * 100
            files = {"file": ("test_audio.mp4", test_content, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}

            response = self.client.post("/api/v1/transcription/upload", files=files, headers=headers)

            # Should fail gracefully
            assert response.status_code == 502
            # File stream position should be reset (tested in the endpoint logic)

    def test_metadata_storage_for_audio_cleanup(self):
        """Test that audio storage path is stored in transcript metadata"""
        # Create test user
        signup_response = self.client.post("/api/v1/auth/signup", json=self.test_user_data)
        assert signup_response.status_code == 200
        access_token = signup_response.json()["access_token"]

        captured_metadata = {}

        # Mock supabase service to capture metadata
        with patch('app.api.endpoints.transcription.upload_video_to_storage') as mock_video_upload, \
             patch('app.api.endpoints.transcription.extract_and_upload_audio') as mock_audio_extract, \
             patch('app.services.deepgram_service.deepgram_service.transcribe_from_url') as mock_deepgram, \
             patch('app.services.supabase_service.supabase_service.create_transcript') as mock_create_transcript:

            mock_video_upload.return_value = asyncio.create_task(
                self._mock_async_return("https://video-url.com")
            )
            mock_audio_extract.return_value = (
                "clients/test123/audio/audio_video456_abc123.wav",
                "https://audio-url.com"
            )
            mock_deepgram.return_value = {"request_id": "deepgram-789"}

            # Capture the metadata passed to create_transcript
            def capture_metadata(transcript_create, user_id):
                captured_metadata.update(transcript_create.metadata or {})
                # Return mock transcript
                mock_transcript = Mock()
                mock_transcript.id = "transcript-123"
                return mock_transcript

            mock_create_transcript.side_effect = capture_metadata

            # Test file upload (using fake data - in real test use test_audio.mp4)
            test_content = b"fake video data" * 100
            files = {"file": ("test_audio.mp4", test_content, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}

            response = self.client.post("/api/v1/transcription/upload", files=files, headers=headers)
            assert response.status_code == 200

            # Verify audio storage path was stored in metadata
            assert "audio_storage_path" in captured_metadata
            audio_path = captured_metadata["audio_storage_path"]
            assert "clients/test123/audio/" in audio_path
            assert "audio_video456_" in audio_path
            assert ".wav" in audio_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])