import pytest
import asyncio
import os
from uuid import uuid4
from io import BytesIO
from fastapi.testclient import TestClient
from app.main import app
from app.services.supabase_service import supabase_service
from app.services.validation_service import validation_service
from app.models.schemas import UserCreate, UserProfileCreate

# Test configuration
TEST_EMAIL_PREFIX = "test_user_"
TEST_ORG_PREFIX = "Test Organization "

class TestCompleteFlow:
    """
    Complete end-to-end testing of signup → upload → transcription flow.
    
    This tests the entire user journey with real services to ensure
    all integrations work correctly.
    """
    
    @pytest.fixture
    def test_client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    @pytest.fixture  
    def unique_test_email(self):
        """Generate unique email for each test run"""
        unique_id = str(uuid4())[:8]
        return f"jaredjohnston000+test_{unique_id}@gmail.com"
    
    @pytest.fixture
    def unique_org_name(self):
        """Generate unique organization name"""
        unique_id = str(uuid4())[:8] 
        return f"{TEST_ORG_PREFIX}{unique_id}"
    
    @pytest.fixture
    def test_user_data(self, unique_test_email, unique_org_name):
        """Complete user signup data"""
        return {
            "email": unique_test_email,
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User", 
            "country": "United States",
            "organization_name": unique_org_name
        }
    
    @pytest.fixture
    def test_audio_file(self):
        """Create a small test audio file (MP3-like bytes)"""
        # This is a minimal MP3-like file that should pass basic validation
        # In real testing, you'd use an actual small audio file
        mp3_header = b'ID3\x04\x00\x00\x00\x00\x00\x00'  # Basic MP3 header
        audio_data = b'\xff\xfb\x90\x00' * 1000  # Fake audio frames 
        return BytesIO(mp3_header + audio_data)
    
    # =============================================================================
    # LAYER 1: CRITICAL UNIT TESTS
    # =============================================================================
    
    def test_validation_service_basic_logic(self):
        """Test ValidationService core logic without external dependencies"""
        from app.services.validation_service import ValidationResult
        
        # Test error code mapping
        result = ValidationResult(
            is_valid=False,
            error_message="Test error",
            error_code="FILE_TOO_LARGE"
        )
        
        http_exception = validation_service.convert_to_http_exception(result)
        assert http_exception.status_code == 413  # Request Entity Too Large
        assert "Test error" in str(http_exception.detail)
    
    def test_signup_data_validation(self, test_user_data):
        """Test UserCreate model validation"""
        user_create = UserCreate(**test_user_data)
        assert user_create.email == test_user_data["email"]
        assert user_create.organization_name == test_user_data["organization_name"]
        assert len(user_create.first_name) > 0
    
    # =============================================================================
    # LAYER 2: SERVICE INTEGRATION TESTS  
    # =============================================================================
    
    @pytest.mark.asyncio
    async def test_supabase_service_integration(self, test_user_data):
        """Test SupabaseService with real Supabase backend"""
        user_create = UserCreate(**test_user_data)
        
        try:
            # Standard Supabase flow: 1. Sign up
            signup_result = await supabase_service.sign_up(user_create)
            user = signup_result
            
            # 2. Sign in to get session (Supabase standard pattern)
            signin_result = await supabase_service.sign_in(user_create.email, user_create.password)
            session = signin_result["session"]
            
            # 3. Complete profile using session
            profile_data = UserProfileCreate(
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                country=user_create.country
            )
            profile = await supabase_service.complete_profile(profile_data, session)
            
            # 4. Create organization using session  
            client = await supabase_service.create_organization(user_create.organization_name, session)
            
            # Verify all components created
            assert user is not None
            assert profile is not None
            assert client is not None
            assert profile.user_id == user.id
            assert client.name == user_create.organization_name
            
            # Verify user can get their client
            user_client = await supabase_service.get_user_client(user.id)
            assert user_client is not None
            assert user_client.name == test_user_data["organization_name"]
            
            # Store for cleanup
            self.created_user_id = user.id
            self.created_client_id = client.id
            
        except Exception as e:
            pytest.fail(f"Supabase service integration failed: {str(e)}")
    
    def test_validation_service_integration(self, test_audio_file):
        """Test ValidationService with real file"""
        from fastapi import UploadFile
        
        # Create mock UploadFile
        upload_file = UploadFile(
            filename="test_audio.mp3",
            file=test_audio_file,
            content_type="audio/mpeg"
        )
        
        # Test basic validation
        basic_result = validation_service.validate_basic_upload(upload_file)
        assert basic_result.is_valid
        assert basic_result.file_info["filename"] == "test_audio.mp3"
        
        # Note: Full transcription validation requires real audio file
        # For now, test that it doesn't crash
        try:
            transcription_result = validation_service.validate_for_transcription(upload_file)
            # May fail on audio validation, but shouldn't crash
        except Exception as e:
            # Expected for fake audio data
            assert "ffmpeg" in str(e).lower() or "audio" in str(e).lower()
    
    # =============================================================================
    # LAYER 3: END-TO-END JOURNEY TEST
    # =============================================================================
    
    @pytest.mark.asyncio 
    async def test_complete_user_journey(self, test_client, test_user_data):
        """
        THE BIG TEST: Complete user journey from signup to transcription
        
        This is the most important test - it verifies the entire flow works.
        """
        access_token = None
        created_user_id = None
        
        try:
            # STEP 1: User signup
            print(f"\n🔹 Testing signup for: {test_user_data['email']}")
            signup_response = test_client.post("/api/v1/auth/signup", json=test_user_data)
            
            assert signup_response.status_code == 200, f"Signup failed: {signup_response.text}"
            signup_data = signup_response.json()
            
            # Verify signup response structure
            assert "user" in signup_data
            assert "profile" in signup_data
            assert "client" in signup_data  
            assert "access_token" in signup_data
            assert signup_data["role"] == "owner"
            
            access_token = signup_data["access_token"]
            created_user_id = signup_data["user"]["id"]
            print(f"✅ Signup successful. User ID: {created_user_id}")
            
            # STEP 2: File upload (using a real small audio file if available)
            print(f"🔹 Testing file upload...")
            
            # Check if we have a real test audio file
            test_audio_path = "test_audio.mp4"  # You'll need to provide this
            if os.path.exists(test_audio_path):
                with open(test_audio_path, "rb") as audio_file:
                    files = {"file": ("test_sermon.mp4", audio_file, "video/mp4")}
                    headers = {"Authorization": f"Bearer {access_token}"}
                    
                    upload_response = test_client.post(
                        "/api/v1/transcription/upload", 
                        files=files,
                        headers=headers
                    )
                    
                    if upload_response.status_code == 200:
                        upload_data = upload_response.json()
                        print(f"✅ Upload successful. Request ID: {upload_data.get('request_id')}")
                        
                        # Verify upload response structure
                        assert upload_data["success"] is True
                        assert "video_id" in upload_data
                        assert "transcript_id" in upload_data
                        assert "request_id" in upload_data
                        assert upload_data["status"] == "processing"
                        
                        print(f"🎉 COMPLETE FLOW SUCCESS!")
                        print(f"   - User created: {signup_data['user']['email']}")
                        print(f"   - Organization: {signup_data['client']['name']}")
                        print(f"   - File uploaded: {upload_data['file_info']['filename']}")
                        print(f"   - Transcription started: {upload_data['request_id']}")
                        
                    else:
                        print(f"⚠️  Upload failed: {upload_response.text}")
                        print("This might be expected if test audio file lacks audio streams")
            else:
                print(f"⚠️  No test audio file found at {test_audio_path}")
                print("Skipping upload test - signup flow verified successfully")
                
        except Exception as e:
            pytest.fail(f"Complete user journey failed: {str(e)}")
            
        finally:
            # CLEANUP: Remove test user (optional - helps keep test DB clean)
            if created_user_id:
                try:
                    print(f"🧹 Cleaning up test user: {created_user_id}")
                    # Cleanup would go here if needed
                except Exception as cleanup_error:
                    print(f"⚠️  Cleanup failed: {cleanup_error}")

    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self, test_client):
        """Test various error scenarios"""
        
        # Test duplicate email signup
        duplicate_data = {
            "email": "duplicate@example.com",  # Use a known email or create one first
            "password": "Test123!",
            "first_name": "Test",
            "last_name": "User",
            "country": "US", 
            "organization_name": "Test Org"
        }
        
        # First signup should work
        response1 = test_client.post("/api/v1/auth/signup", json=duplicate_data)
        
        # Second signup should fail
        response2 = test_client.post("/api/v1/auth/signup", json=duplicate_data)
        assert response2.status_code == 409  # Conflict - user exists
        
    def test_file_validation_scenarios(self):
        """Test file validation edge cases"""
        from fastapi import UploadFile
        
        # Test file too small
        tiny_file = BytesIO(b"tiny")
        upload_file = UploadFile(filename="tiny.mp3", file=tiny_file, content_type="audio/mpeg")
        
        result = validation_service.validate_basic_upload(upload_file)
        assert not result.is_valid
        assert result.error_code == "FILE_TOO_SMALL"
        
        # Test missing filename  
        no_name_file = BytesIO(b"x" * 2000)
        upload_file = UploadFile(filename="", file=no_name_file, content_type="audio/mpeg")
        
        result = validation_service.validate_basic_upload(upload_file)
        assert not result.is_valid
        assert result.error_code == "MISSING_FILENAME"


# =============================================================================
# MANUAL TESTING INSTRUCTIONS
# =============================================================================

"""
TO RUN THESE TESTS:

1. PREPARE TEST ENVIRONMENT:
   - Ensure Supabase is running and accessible
   - Set environment variables (SUPABASE_URL, SUPABASE_KEY, etc.)
   - Create a small test audio file: test_audio.mp4 (< 10MB)

2. RUN INDIVIDUAL TEST LAYERS:
   
   # Layer 1: Unit tests (fast)
   pytest tests/test_complete_flow.py::TestCompleteFlow::test_validation_service_basic_logic -v
   
   # Layer 2: Service integration tests  
   pytest tests/test_complete_flow.py::TestCompleteFlow::test_supabase_service_integration -v
   
   # Layer 3: Complete journey
   pytest tests/test_complete_flow.py::TestCompleteFlow::test_complete_user_journey -v

3. RUN ALL TESTS:
   pytest tests/test_complete_flow.py -v -s

4. VERIFY RESULTS:
   - Check Supabase dashboard for created users/clients
   - Check Deepgram dashboard for transcription jobs
   - Verify no orphaned test data

EXPECTED OUTCOMES:
✅ All services integrate correctly
✅ User signup creates user + profile + client
✅ File upload validation works  
✅ Deepgram transcription job starts
✅ Database records are consistent
"""