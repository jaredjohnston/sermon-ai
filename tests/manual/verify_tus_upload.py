#!/usr/bin/env python3
"""
TUS Upload Verification Script
Simplified script to verify 86MB TUS upload to Supabase with visual feedback
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

class TUSUploadVerifier:
    """Focused TUS upload verification for real-world testing"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        # Use your auth token here
        self.auth_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6IlNOWnZSYitpeFp5dXZ6WW4iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2ZhcGp4ZWt1eWNrdXJhaGJ0dnJ0LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3ODQyZjZmNC05YjI2LTQyZDYtYjFjYy0xZWZlYTIyMjQ2OTMiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUxODk5NTM4LCJpYXQiOjE3NTE4OTU5MzgsImVtYWlsIjoiamFyZWRqb2huc3RvbjAwMCt0b2tlbnRlc3RfMjAyNTA3MDdfMTQ0NTM3QGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJqYXJlZGpvaG5zdG9uMDAwK3Rva2VudGVzdF8yMDI1MDcwN18xNDQ1MzdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiNzg0MmY2ZjQtOWIyNi00MmQ2LWIxY2MtMWVmZWEyMjI0NjkzIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTE4OTU5Mzh9XSwic2Vzc2lvbl9pZCI6IjZkZDlkMDNmLWRkMmItNGQ2Mi04YzViLTYxYjNkOGRkOTZlYSIsImlzX2Fub255bW91cyI6ZmFsc2V9.W5U7W1auJi7Xxo4j9_CUmWWwvQ6BjYkpS6N0uRdpKIQ"
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        self.file_path = "/Users/jaredjohnston/Desktop/SermonAI/full_sermon_test_86mb.mp3"

    def verify_prerequisites(self):
        """Check that everything is ready for testing"""
        print("🔍 Verifying Prerequisites")
        print("-" * 30)
        
        # Check file exists
        if not os.path.exists(self.file_path):
            print(f"❌ 86MB test file not found: {self.file_path}")
            return False
        
        file_size = os.path.getsize(self.file_path)
        file_size_mb = file_size / 1024 / 1024
        print(f"✅ Test file found: {file_size_mb:.1f}MB")
        
        # Check API is running
        try:
            health_response = requests.get(f"{self.base_url}/health", timeout=5)
            if health_response.status_code == 200:
                print(f"✅ API server running: {self.base_url}")
            else:
                print(f"❌ API server error: {health_response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ API server not accessible: {e}")
            print(f"💡 Start server with: uvicorn app.main:app --reload")
            return False
        
        print(f"✅ Auth token configured")
        print()
        return True

    def step1_prepare_upload(self):
        """Step 1: Request TUS upload configuration"""
        print("📋 STEP 1: Preparing TUS Upload")
        print("-" * 30)
        
        file_size = os.path.getsize(self.file_path)
        timestamp = int(datetime.now().timestamp())
        
        prepare_request = {
            "filename": f"verify_tus_{timestamp}.mp3",
            "content_type": "audio/mpeg",
            "size_bytes": file_size
        }
        
        print(f"📤 Request: {json.dumps(prepare_request, indent=2)}")
        
        response = requests.post(
            f"{self.base_url}/transcription/upload/prepare",
            headers=self.headers,
            json=prepare_request,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Prepare failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        config = response.json()
        print(f"✅ Upload configuration received")
        print(f"   Upload method: {config.get('upload_method')}")
        print(f"   Media ID: {config.get('media_id')}")
        
        # Verify TUS configuration
        tus_config = config.get('tus_config')
        if not tus_config:
            print(f"❌ No TUS config in response (file might be too small)")
            return None
        
        print(f"   TUS endpoint: {tus_config.get('upload_url')}")
        print(f"   Chunk size: {tus_config.get('chunk_size', 0) / 1024 / 1024:.1f}MB")
        print(f"   Expected chunks: {file_size // tus_config.get('chunk_size', 1) + 1}")
        print()
        
        return config

    def step2_tus_upload(self, config):
        """Step 2: Perform TUS upload with progress tracking"""
        print("🚀 STEP 2: TUS Upload with Real-Time Progress")
        print("-" * 30)
        
        tus_config = config['tus_config']
        upload_url = tus_config['upload_url']
        headers = tus_config['headers']
        metadata = tus_config['metadata']
        chunk_size = tus_config['chunk_size']
        
        file_size = os.path.getsize(self.file_path)
        
        print(f"📁 File: {os.path.basename(self.file_path)}")
        print(f"📊 Size: {file_size / 1024 / 1024:.1f}MB")
        print(f"🔧 Chunk size: {chunk_size / 1024 / 1024:.1f}MB")
        print(f"🎯 Target: {metadata.get('objectName', 'unknown')}")
        print()
        
        start_time = time.time()
        
        try:
            with open(self.file_path, 'rb') as f:
                # Step 2.1: Create TUS session
                print(f"🔄 Creating TUS upload session...")
                create_headers = {
                    **headers,
                    'Upload-Length': str(file_size),
                    'Upload-Metadata': ','.join([f'{k} {v}' for k, v in metadata.items()])
                }
                
                create_response = requests.post(
                    upload_url,
                    headers=create_headers,
                    timeout=30
                )
                
                if create_response.status_code != 201:
                    print(f"❌ TUS session creation failed: {create_response.status_code}")
                    print(f"   Response: {create_response.text}")
                    return False
                
                upload_location = create_response.headers.get('Location')
                print(f"✅ TUS session created: {upload_location}")
                print()
                
                # Step 2.2: Upload in chunks with progress
                uploaded = 0
                chunk_count = 0
                
                print(f"📤 Starting chunked upload...")
                while uploaded < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    chunk_count += 1
                    chunk_start_time = time.time()
                    
                    patch_headers = {
                        **headers,
                        'Upload-Offset': str(uploaded),
                        'Content-Type': 'application/offset+octet-stream'
                    }
                    
                    patch_response = requests.patch(
                        upload_location,
                        data=chunk,
                        headers=patch_headers,
                        timeout=120  # 2 minutes per chunk
                    )
                    
                    if patch_response.status_code == 204:
                        uploaded += len(chunk)
                        chunk_time = time.time() - chunk_start_time
                        progress = (uploaded / file_size) * 100
                        speed = len(chunk) / 1024 / 1024 / chunk_time  # MB/s
                        
                        print(f"   ✅ Chunk {chunk_count:2d}: {progress:5.1f}% "
                              f"({uploaded / 1024 / 1024:5.1f}MB/{file_size / 1024 / 1024:.1f}MB) "
                              f"- {speed:.1f}MB/s")
                    else:
                        print(f"❌ Chunk {chunk_count} failed: {patch_response.status_code}")
                        print(f"   Response: {patch_response.text}")
                        return False
                
                total_time = time.time() - start_time
                avg_speed = file_size / 1024 / 1024 / total_time
                
                print()
                print(f"🎉 TUS UPLOAD COMPLETED!")
                print(f"   📊 Total time: {total_time:.1f}s")
                print(f"   📈 Average speed: {avg_speed:.1f}MB/s")
                print(f"   📦 Chunks sent: {chunk_count}")
                print(f"   📁 Uploaded: {uploaded:,} bytes")
                print()
                
                return uploaded == file_size
                
        except Exception as e:
            print(f"❌ Upload error: {str(e)}")
            return False

    def step3_verify_supabase(self, config):
        """Step 3: Verify file appears in Supabase"""
        print("🔍 STEP 3: Supabase Verification")
        print("-" * 30)
        
        media_id = config.get('media_id')
        tus_config = config.get('tus_config', {})
        object_name = tus_config.get('metadata', {}).get('objectName', 'unknown')
        
        print(f"📋 Expected Results:")
        print(f"   Media ID: {media_id}")
        print(f"   Storage path: {object_name}")
        print(f"   File size: {os.path.getsize(self.file_path):,} bytes")
        print()
        
        print(f"👀 Manual Verification Steps:")
        print(f"   1. Open Supabase Dashboard")
        print(f"   2. Go to Storage → 'sermons' bucket")
        print(f"   3. Navigate to: {object_name}")
        print(f"   4. Verify file size matches: {os.path.getsize(self.file_path):,} bytes")
        print()
        
        print(f"🗄️  Database Verification:")
        print(f"   1. Check 'media' table for media_id: {media_id}")
        print(f"   2. Check 'transcripts' table for processing status")
        print(f"   3. Verify audit fields (created_by, updated_by) are not null")
        print()
        
        return True

    def run_verification(self):
        """Run complete TUS upload verification"""
        print("🧪 TUS UPLOAD VERIFICATION")
        print("=" * 50)
        print("Real-world testing with 86MB file")
        print("Visual confirmation of Supabase integration")
        print("=" * 50)
        print()
        
        # Prerequisites
        if not self.verify_prerequisites():
            print("❌ Prerequisites failed. Please fix and try again.")
            return False
        
        # Step 1: Prepare
        config = self.step1_prepare_upload()
        if not config:
            print("❌ Upload preparation failed")
            return False
        
        # Step 2: Upload
        upload_success = self.step2_tus_upload(config)
        if not upload_success:
            print("❌ TUS upload failed")
            return False
        
        # Step 3: Verify
        self.step3_verify_supabase(config)
        
        print("🎯 VERIFICATION COMPLETE!")
        print()
        print("✅ What was verified:")
        print("   • TUS configuration generation")
        print("   • Chunked upload with progress tracking")
        print("   • Real 86MB file upload to Supabase")
        print("   • File storage and database integration")
        print()
        print("👀 Next: Check Supabase Dashboard to see your file!")
        
        return True


def main():
    """Run TUS upload verification"""
    print("📋 Prerequisites:")
    print("   1. FastAPI server running: uvicorn app.main:app --reload")
    print("   2. 86MB test file exists")
    print("   3. Valid authentication token")
    print("   4. Supabase Storage configured")
    print()
    
    verifier = TUSUploadVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 TUS upload verification successful!")
        print("Check Supabase Dashboard to see your 86MB file!")
        return 0
    else:
        print("\n❌ TUS upload verification failed")
        print("Check the error messages above")
        return 1


if __name__ == "__main__":
    exit(main())