#!/usr/bin/env python3
"""Debug script to test the transcript_with_media view"""

import os
import sys
from supabase import create_client

# Add the backend directory to the path
sys.path.append('/Users/jaredjohnston/sermon_ai/backend')

from app.config.settings import settings

def test_view():
    """Test the transcript_with_media view directly"""
    try:
        print("🔍 Testing Supabase transcript_with_media view...")
        
        # Create Supabase client with service role key
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Test 1: Check if view exists and has data
        print("\n1. Testing view access...")
        response = supabase.table('transcript_with_media').select('*').limit(3).execute()
        
        if response.data:
            print(f"✅ View has {len(response.data)} rows")
            print(f"✅ Sample row columns: {list(response.data[0].keys())}")
            
            # Check for filename field specifically
            if 'filename' in response.data[0]:
                print(f"✅ Filename field present: '{response.data[0]['filename']}'")
            else:
                print("❌ ERROR: No filename field in view!")
                
            # Show first row for debugging
            print(f"\n📋 Sample row: {response.data[0]}")
        else:
            print("❌ ERROR: View has no data!")
        
        # Test 2: Check media table has filenames
        print("\n2. Testing media table...")
        media_response = supabase.table('media').select('id, filename').limit(3).execute()
        
        if media_response.data:
            print(f"✅ Media table has {len(media_response.data)} rows")
            for media in media_response.data:
                print(f"   Media {media['id']}: {media['filename']}")
        else:
            print("❌ ERROR: Media table has no data!")
            
        # Test 3: Check transcripts table
        print("\n3. Testing transcripts table...")
        transcript_response = supabase.table('transcripts').select('id, media_id').limit(3).execute()
        
        if transcript_response.data:
            print(f"✅ Transcripts table has {len(transcript_response.data)} rows")
            for transcript in transcript_response.data:
                print(f"   Transcript {transcript['id']}: media_id = {transcript['media_id']}")
        else:
            print("❌ ERROR: Transcripts table has no data!")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_view()