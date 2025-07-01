#!/usr/bin/env python3
"""
Quick test script for Phase 1 content templates functionality
Tests the API endpoints we just created
"""
import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"test_templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_PASSWORD = "TestTemplates2024!"

class TemplateAPITester:
    def __init__(self):
        self.access_token = None
        self.client_id = None
        self.user_id = None
        self.created_template_id = None

    def test_signup_and_auth(self):
        """Test user signup to get authentication token"""
        print("🔹 Testing user signup and authentication...")
        
        signup_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "first_name": "Template",
            "last_name": "Tester",
            "country": "United States",
            "organization_name": "Test Church for Templates"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.client_id = data.get("client", {}).get("id")
                self.user_id = data.get("user", {}).get("id")
                
                print(f"✅ Signup successful!")
                print(f"   Client ID: {self.client_id}")
                print(f"   User ID: {self.user_id}")
                print(f"   Token: {self.access_token[:20]}...")
                return True
            else:
                print(f"❌ Signup failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Signup error: {str(e)}")
            return False

    def get_auth_headers(self):
        """Get authentication headers for API requests"""
        return {"Authorization": f"Bearer {self.access_token}"}

    def test_create_template(self):
        """Test creating a new content template"""
        print("\n🔹 Testing template creation...")
        
        template_data = {
            "client_id": self.client_id,
            "name": "Test Small Group Guide",
            "description": "A test template for small group discussion guides",
            "content_type_name": "small_group_guide",
            "structured_prompt": "Create a small group discussion guide based on the sermon transcript. Include: 1) Brief summary (2-3 sentences), 2) Key scripture references, 3) 4-5 discussion questions for personal reflection and group sharing, 4) One practical application challenge for the week. Keep the tone conversational and encouraging.",
            "example_content": [
                "Example small group guide from our church...",
                "Another example showing our style..."
            ]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/content/templates",
                json=template_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 201:
                data = response.json()
                self.created_template_id = data.get("id")
                print(f"✅ Template created successfully!")
                print(f"   Template ID: {self.created_template_id}")
                print(f"   Name: {data.get('name')}")
                print(f"   Content Type: {data.get('content_type_name')}")
                print(f"   Status: {data.get('status')}")
                return True
            else:
                print(f"❌ Template creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Template creation error: {str(e)}")
            return False

    def test_list_templates(self):
        """Test listing templates for the organization"""
        print("\n🔹 Testing template listing...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/content/templates",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                templates = response.json()
                print(f"✅ Template listing successful!")
                print(f"   Found {len(templates)} templates")
                
                for template in templates:
                    print(f"   • {template['name']} ({template['content_type_name']}) - {template['status']}")
                
                return True
            else:
                print(f"❌ Template listing failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Template listing error: {str(e)}")
            return False

    def test_get_template_by_id(self):
        """Test retrieving a specific template by ID"""
        if not self.created_template_id:
            print("\n⚠️  Skipping template retrieval test - no template ID available")
            return False
            
        print(f"\n🔹 Testing template retrieval by ID...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/content/templates/{self.created_template_id}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                template = response.json()
                print(f"✅ Template retrieval successful!")
                print(f"   ID: {template['id']}")
                print(f"   Name: {template['name']}")
                print(f"   Prompt length: {len(template['structured_prompt'])} characters")
                print(f"   Examples: {len(template['example_content'])} provided")
                return True
            else:
                print(f"❌ Template retrieval failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Template retrieval error: {str(e)}")
            return False

    def test_update_template(self):
        """Test updating a template"""
        if not self.created_template_id:
            print("\n⚠️  Skipping template update test - no template ID available")
            return False
            
        print(f"\n🔹 Testing template update...")
        
        update_data = {
            "description": "Updated description for testing purposes",
            "status": "draft"
        }
        
        try:
            response = requests.put(
                f"{BASE_URL}/content/templates/{self.created_template_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                template = response.json()
                print(f"✅ Template update successful!")
                print(f"   New description: {template['description']}")
                print(f"   New status: {template['status']}")
                return True
            else:
                print(f"❌ Template update failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Template update error: {str(e)}")
            return False

    def test_extract_endpoint_placeholder(self):
        """Test the pattern extraction endpoint (should return 501 Not Implemented)"""
        print("\n🔹 Testing pattern extraction endpoint (should be not implemented)...")
        
        extract_data = {
            "content_type_name": "test_type",
            "examples": ["Example 1", "Example 2"],
            "description": "Test extraction"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/content/templates/extract",
                json=extract_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 501:
                print(f"✅ Pattern extraction endpoint correctly returns 501 Not Implemented")
                print(f"   Message: {response.json().get('detail', 'No detail')}")
                return True
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Pattern extraction test error: {str(e)}")
            return False

def run_template_tests():
    """Run all template API tests"""
    print("🚀 CONTENT TEMPLATES API TESTS")
    print("=" * 50)
    
    tester = TemplateAPITester()
    test_results = {}
    
    # Test authentication first
    test_results['auth'] = tester.test_signup_and_auth()
    
    if test_results['auth']:
        # Run template tests
        test_results['create'] = tester.test_create_template()
        test_results['list'] = tester.test_list_templates()
        test_results['get_by_id'] = tester.test_get_template_by_id()
        test_results['update'] = tester.test_update_template()
        test_results['extract_placeholder'] = tester.test_extract_endpoint_placeholder()
    else:
        print("❌ Skipping template tests due to authentication failure")
        return False
    
    # Results summary
    print("\n" + "=" * 50)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    test_names = [
        ("User Authentication", test_results.get('auth', False)),
        ("Template Creation", test_results.get('create', False)),
        ("Template Listing", test_results.get('list', False)),
        ("Template Retrieval", test_results.get('get_by_id', False)),
        ("Template Update", test_results.get('update', False)),
        ("Extract Endpoint (501)", test_results.get('extract_placeholder', False))
    ]
    
    passed = 0
    for test_name, success in test_names:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 SUMMARY: {passed}/{len(test_names)} tests passed")
    
    if passed == len(test_names):
        print("🎉 ALL TESTS PASSED! Phase 1 content templates working correctly!")
    else:
        print(f"⚠️  {len(test_names) - passed} test(s) failed - check implementation")
    
    return passed == len(test_names)

if __name__ == "__main__":
    print("💡 Make sure FastAPI server is running on localhost:8000")
    print("   Start with: uvicorn app.main:app --reload")
    print()
    
    try:
        # Quick health check
        response = requests.get("http://localhost:8000/api/v1/health")
        if response.status_code != 200:
            print("❌ FastAPI server not responding. Please start the server first.")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server. Please start with:")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)
    
    run_template_tests()