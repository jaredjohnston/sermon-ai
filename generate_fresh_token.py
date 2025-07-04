#!/usr/bin/env python3
"""
Generate a fresh JWT token for manual testing
Creates a new user and prints the token for copy-paste
"""

import requests
import json
from datetime import datetime

def create_user_and_get_token():
    """Create new user and return fresh JWT token"""
    
    # Generate unique timestamp for email
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # User data
    user_data = {
        "email": f"jaredjohnston000+tokentest_{timestamp}@gmail.com",
        "password": "TestSermonAI2024!",
        "first_name": "Token",
        "last_name": "Test",
        "country": "United States",
        "organization_name": "Token Test Church"
    }
    
    print("🔑 CREATING FRESH USER & TOKEN")
    print("=" * 50)
    print(f"📧 Email: {user_data['email']}")
    
    # Make signup request
    response = requests.post(
        "http://localhost:8000/api/v1/auth/signup",
        json=user_data,
        timeout=30
    )
    
    print(f"📋 Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ SUCCESS! New user created")
        print(f"\n🆔 USER DETAILS:")
        print(f"   User ID: {data['user']['id']}")
        print(f"   Client ID: {data['client']['id']}")
        print(f"   Organization: {data['client']['name']}")
        
        # Get the fresh token
        token = data['access_token']
        
        print(f"\n🔑 FRESH JWT TOKEN:")
        print("=" * 50)
        print(token)
        print("=" * 50)
        
        print(f"\n📋 COPY THIS TOKEN TO test_new_upload_system.py:")
        print(f"   Line 18: Replace the token in self.headers")
        print(f"   File location: /Users/jaredjohnston/sermon_ai/test_new_upload_system.py")
        
        return {
            'token': token,
            'user_id': data['user']['id'],
            'client_id': data['client']['id'],
            'email': user_data['email']
        }
    else:
        print(f"❌ FAILED: {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == "__main__":
    result = create_user_and_get_token()
    
    if result:
        print(f"\n✅ Ready for testing!")
        print(f"   1. Copy the token above")
        print(f"   2. Paste into test_new_upload_system.py")
        print(f"   3. Run: python test_new_upload_system.py")
    else:
        print(f"\n❌ Failed to create user. Check if server is running.")