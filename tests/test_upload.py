import os
import time
import pytest
import httpx
from uuid import UUID
from app.services.supabase_service import supabase_service
from app.models.schemas import UserCreate, ClientCreate

# Test user credentials
TEST_USER_EMAIL = "jaredjohnston000+uploadtest@gmail.com"
TEST_USER_PASSWORD = "Test123!@#"

def confirm_user_email(email: str):
    """Confirm a user's email using Supabase admin API"""
    try:
        # Get user by email
        users = supabase_service.client.auth.admin.list_users()
        user = next((u for u in users.users if u.email == email), None)
        
        if user and not user.email_confirmed_at:
            # Confirm the user's email
            supabase_service.client.auth.admin.update_user_by_id(
                user.id,
                {"email_confirm": True}
            )
            print(f"Confirmed email for user: {email}")
            return True
        return False
    except Exception as e:
        print(f"Failed to confirm email: {str(e)}")
        return False

def test_video_upload_flow():
    """Test the complete video upload flow"""
    print("\nStarting video upload test...")
    
    # 1. Create test user or sign in if exists
    print("Creating test user...")
    try:
        # Try to sign in first
        auth_response = supabase_service.sign_in(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        user = auth_response["user"]
        print(f"User already exists, signed in with ID: {user.id}")
    except Exception as e:
        # If sign in fails, try to create user
        try:
            user = supabase_service.sign_up(UserCreate(
                email=TEST_USER_EMAIL,
                password=TEST_USER_PASSWORD
            ))
            print(f"Created new user with ID: {user.id}")
            
            # Try to confirm the email
            if confirm_user_email(TEST_USER_EMAIL):
                print("Email confirmed successfully")
            else:
                print("Could not confirm email automatically. Please confirm manually in Supabase dashboard.")
                pytest.skip("Email confirmation required")
            
            # Wait a moment for the confirmation to take effect
            time.sleep(2)
            
        except Exception as signup_error:
            if "429" in str(signup_error):
                print("Rate limited by Supabase. Please wait a few minutes and try again.")
                pytest.skip("Rate limited by Supabase")
            else:
                raise
    
    # 2. Create test client
    print("Creating test client...")
    try:
        client = supabase_service.create_client("Test Church", user.id)
        print(f"Created client with ID: {client.id}")
    except Exception as e:
        if "already exists" in str(e).lower():
            # Get existing client
            client = supabase_service.get_user_client(user.id)
            print(f"Using existing client with ID: {client.id}")
        else:
            raise
    
    # 3. Verify user is associated with client
    print("Verifying user-client association...")
    user_client = supabase_service.get_user_client(user.id)
    assert user_client is not None, "User should be associated with a client"
    assert user_client.id == client.id, "User should be associated with the test client"
    print("User-client association verified")
    
    # 4. Create a small test video file
    print("Creating test video file...")
    test_video_path = "test_video.mp4"
    with open(test_video_path, "wb") as f:
        f.write(b"\0" * 1024 * 1024)  # 1MB of zeros
    print(f"Created test video file at {test_video_path}")
    
    try:
        # 5. Test the upload endpoint
        print("Testing video upload endpoint...")
        # Get fresh auth token
        auth_response = supabase_service.sign_in(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        token = auth_response["session"].access_token
        
        # Make the upload request
        with httpx.Client() as client:
            response = client.post(
                "http://localhost:8000/api/videos/upload",
                files={"file": ("test_video.mp4", open(test_video_path, "rb"), "video/mp4")},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200, f"Upload failed with status {response.status_code}: {response.text}"
            print("Video upload successful!")
            
            # Verify video was created in database
            video_data = response.json()
            assert "id" in video_data, "Response should include video ID"
            print(f"Video created with ID: {video_data['id']}")
            
    finally:
        # 6. Clean up
        print("Cleaning up...")
        if os.path.exists(test_video_path):
            os.remove(test_video_path)
            print("Test video file removed")

if __name__ == "__main__":
    test_video_upload_flow() 