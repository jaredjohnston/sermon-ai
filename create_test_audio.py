#!/usr/bin/env python3
"""
Generate a small test audio file for testing the transcription pipeline.

This creates a minimal but valid MP3 file that Deepgram can process.
"""

import os
import subprocess
import sys

def create_test_audio():
    """Create a small test audio file using ffmpeg"""
    
    output_file = "test_audio.mp3"
    
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install ffmpeg first:")
        print("   macOS: brew install ffmpeg")
        print("   Ubuntu: sudo apt install ffmpeg")
        return False
    
    # Generate a 10-second sine wave audio file (440Hz - A note)
    cmd = [
        "ffmpeg", "-y",  # Overwrite output file
        "-f", "lavfi",   # Use libavfilter input
        "-i", "sine=frequency=440:duration=10",  # 440Hz sine wave, 10 seconds
        "-ac", "1",      # Mono audio
        "-ar", "22050",  # 22kHz sample rate (lower quality = smaller file)
        "-b:a", "32k",   # 32kbps bitrate (small file size)
        output_file
    ]
    
    try:
        print(f"🔹 Creating test audio file: {output_file}")
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Check file size
        size_bytes = os.path.getsize(output_file)
        size_kb = size_bytes / 1024
        
        print(f"✅ Test audio file created successfully!")
        print(f"   File: {output_file}")
        print(f"   Size: {size_kb:.1f} KB")
        print(f"   Duration: 10 seconds")
        print(f"   Format: MP3, 440Hz sine wave")
        print(f"\nThis file can be used for testing transcription uploads.")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create audio file: {e}")
        return False

def create_test_video():
    """Create a small test video file with audio"""
    
    output_file = "test_video.mp4"
    
    # Generate a 5-second video with audio
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=blue:size=320x240:duration=5",  # Blue video
        "-f", "lavfi", 
        "-i", "sine=frequency=440:duration=5",         # Audio track
        "-c:v", "libx264", "-preset", "ultrafast",     # Fast video encoding
        "-c:a", "aac", "-b:a", "32k",                  # Audio encoding
        "-shortest",                                    # Stop when shortest stream ends
        output_file
    ]
    
    try:
        print(f"🔹 Creating test video file: {output_file}")
        subprocess.run(cmd, capture_output=True, check=True)
        
        size_bytes = os.path.getsize(output_file)
        size_kb = size_bytes / 1024
        
        print(f"✅ Test video file created successfully!")
        print(f"   File: {output_file}")
        print(f"   Size: {size_kb:.1f} KB") 
        print(f"   Duration: 5 seconds")
        print(f"   Format: MP4 with audio track")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create video file: {e}")
        return False

if __name__ == "__main__":
    print("🎵 SERMONAI TEST AUDIO GENERATOR")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "video":
        create_test_video()
    else:
        create_test_audio()
        
    print(f"\nUsage:")
    print(f"  python create_test_audio.py        # Create MP3 audio file")
    print(f"  python create_test_audio.py video  # Create MP4 video file")