import pytest
from io import BytesIO
import ffmpeg
from unittest.mock import Mock, patch
from app.services.deepgram_service import DeepgramService

@pytest.fixture
def deepgram_service():
    """Create a DeepgramService instance for testing"""
    return DeepgramService()

@pytest.fixture
def mock_ffmpeg_probe():
    """Mock for ffmpeg.probe with configurable return values"""
    with patch('ffmpeg.probe') as mock_probe:
        yield mock_probe

def test_validate_audio_with_valid_audio(deepgram_service, mock_ffmpeg_probe):
    """Test validation with a file containing audio streams"""
    # Mock ffmpeg.probe to return a response with audio streams
    mock_ffmpeg_probe.return_value = {
        'streams': [
            {'codec_type': 'audio', 'codec_name': 'aac'},
            {'codec_type': 'video', 'codec_name': 'h264'}
        ]
    }
    
    # Create a dummy file-like object
    test_file = BytesIO(b"test content")
    
    # Validate should return True
    assert deepgram_service._validate_audio(test_file) is True
    
    # Verify probe was called
    mock_ffmpeg_probe.assert_called_once()

def test_validate_audio_without_audio(deepgram_service, mock_ffmpeg_probe):
    """Test validation with a file containing no audio streams"""
    # Mock ffmpeg.probe to return a response without audio streams
    mock_ffmpeg_probe.return_value = {
        'streams': [
            {'codec_type': 'video', 'codec_name': 'h264'}
        ]
    }
    
    # Create a dummy file-like object
    test_file = BytesIO(b"test content")
    
    # Validate should return False
    assert deepgram_service._validate_audio(test_file) is False

def test_validate_audio_with_ffmpeg_error(deepgram_service, mock_ffmpeg_probe):
    """Test validation when ffmpeg.probe raises an error"""
    # Mock ffmpeg.probe to raise an error
    mock_ffmpeg_probe.side_effect = ffmpeg.Error(
        cmd="ffmpeg -i test.mp4",
        stdout=b"",
        stderr=b"FFmpeg error"
    )
    
    # Create a dummy file-like object
    test_file = BytesIO(b"test content")
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="Invalid file format or corrupted file"):
        deepgram_service._validate_audio(test_file)

def test_validate_audio_preserves_file_position(deepgram_service, mock_ffmpeg_probe):
    """Test that file position is preserved after validation"""
    # Mock ffmpeg.probe to return valid response
    mock_ffmpeg_probe.return_value = {
        'streams': [
            {'codec_type': 'audio', 'codec_name': 'aac'}
        ]
    }
    
    # Create a file with some content and move position
    test_file = BytesIO(b"test content")
    test_file.seek(5)  # Move to position 5
    original_position = test_file.tell()
    
    # Validate audio
    deepgram_service._validate_audio(test_file)
    
    # Verify position is preserved
    assert test_file.tell() == original_position

def test_validate_audio_with_empty_streams(deepgram_service, mock_ffmpeg_probe):
    """Test validation with empty streams list"""
    # Mock ffmpeg.probe to return empty streams
    mock_ffmpeg_probe.return_value = {
        'streams': []
    }
    
    # Create a dummy file-like object
    test_file = BytesIO(b"test content")
    
    # Validate should return False
    assert deepgram_service._validate_audio(test_file) is False 