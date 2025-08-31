#!/usr/bin/env python3
"""
Test script to verify Django API error responses
This script tests the API endpoints to ensure they return proper error structures
"""

import requests
import json
import sys
import os

# Add the Django project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
import django
django.setup()

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust if your Django server runs on different port
API_BASE = f"{BASE_URL}/api/v1"

def test_api_error_response(endpoint, data, expected_status=400, description=""):
    """Test an API endpoint and verify error response structure"""
    print(f"\n🔍 Testing: {description}")
    print(f"📡 Endpoint: {endpoint}")
    print(f"📤 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(f"{API_BASE}{endpoint}", json=data)
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response structure
        if response.status_code == expected_status:
            response_data = response.json()
            
            # Check if response has the expected error structure
            if "success" in response_data and response_data["success"] == False:
                if "error" in response_data:
                    error = response_data["error"]
                    if "code" in error and "message" in error and "type" in error:
                        print("✅ SUCCESS: Proper error structure returned")
                        print(f"   Code: {error['code']}")
                        print(f"   Message: {error['message']}")
                        print(f"   Type: {error['type']}")
                        return True
                    else:
                        print("❌ FAIL: Error object missing required fields")
                        print(f"   Error object: {error}")
                        return False
                else:
                    print("❌ FAIL: No 'error' key in response")
                    return False
            else:
                print("❌ FAIL: Response not marked as unsuccessful")
                return False
        else:
            print(f"❌ FAIL: Expected status {expected_status}, got {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: Could not connect to Django server")
        print("   Make sure Django is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False

def main():
    """Run all API error tests"""
    print("🚀 Starting Django API Error Response Tests")
    print("=" * 50)
    
    tests = [
        # Registration tests
        {
            "endpoint": "/auth/register/step1/",
            "data": {"email": "invalid-email"},
            "expected_status": 400,
            "description": "Invalid email format"
        },
        {
            "endpoint": "/auth/register/step1/",
            "data": {"email": "test@example.com"},
            "expected_status": 200,
            "description": "Valid email (should succeed)"
        },
        {
            "endpoint": "/auth/register/step1/",
            "data": {"email": "test@example.com"},
            "expected_status": 409,
            "description": "Duplicate email (should fail with conflict)"
        },
        
        # Username availability test
        {
            "endpoint": "/auth/check-username/",
            "data": {"username": "a"},
            "expected_status": 400,
            "description": "Username too short"
        },
        {
            "endpoint": "/auth/check-username/",
            "data": {"username": "testuser"},
            "expected_status": 200,
            "description": "Valid username (should succeed)"
        },
        
        # Login tests
        {
            "endpoint": "/auth/login/",
            "data": {"identifier": "nonexistent"},
            "expected_status": 404,
            "description": "Non-existent user"
        },
        {
            "endpoint": "/auth/login/",
            "data": {"identifier": "testuser", "password": "wrongpassword"},
            "expected_status": 401,
            "description": "Wrong password"
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test_api_error_response(**test):
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API error responses are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the Django API implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
