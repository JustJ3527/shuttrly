#!/usr/bin/env python3
"""
Debug script to test Django API error responses
Run this from the Django shell: python manage.py shell < debug_api_errors.py
"""

from django.test import Client
from django.urls import reverse
import json

def test_api_errors():
    """Test API endpoints and verify error response structures"""
    client = Client()
    
    print("🚀 Testing Django API Error Responses")
    print("=" * 50)
    
    # Test 1: Invalid email format
    print("\n🔍 Test 1: Invalid email format")
    response = client.post('/api/v1/auth/register/step1/', 
                          data=json.dumps({"email": "invalid-email"}),
                          content_type='application/json')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")
    
    # Test 2: Username too short
    print("\n🔍 Test 2: Username too short")
    response = client.post('/api/v1/auth/check-username/',
                          data=json.dumps({"username": "a"}),
                          content_type='application/json')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")
    
    # Test 3: Non-existent user login
    print("\n🔍 Test 3: Non-existent user login")
    response = client.post('/api/v1/auth/login/',
                          data=json.dumps({"identifier": "nonexistent", "password": "testpass"}),
                          content_type='application/json')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")
    
    # Test 4: Missing required fields
    print("\n🔍 Test 4: Missing required fields")
    response = client.post('/api/v1/auth/register/step1/',
                          data=json.dumps({}),
                          content_type='application/json')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")

if __name__ == "__main__":
    test_api_errors()
