#!/usr/bin/env python3
"""
Test script to verify Django registration fix
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
django.setup()

from users.models import CustomUser
from django.utils import timezone
import uuid

def test_user_creation():
    """Test that CustomUser can be created with correct fields"""
    try:
        # Test creating a temporary user for registration
        temp_username = f"test_{uuid.uuid4().hex[:8]}"
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        temp_user = CustomUser.objects.create(
            email=test_email,
            username=temp_username,
            first_name="",
            last_name="",
            is_active=False,
            email_verification_code="123456",  # Fixed field name
            verification_code_sent_at=timezone.now()
        )
        
        print(f"✅ Successfully created test user: {temp_user.username}")
        print(f"   Email: {temp_user.email}")
        print(f"   Verification code: {temp_user.email_verification_code}")
        
        # Clean up
        temp_user.delete()
        print("✅ Test user cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

def test_model_fields():
    """Test that all required fields exist in CustomUser model"""
    try:
        # Check if the field exists
        field_names = [field.name for field in CustomUser._meta.get_fields()]
        
        required_fields = [
            'email_verification_code',
            'verification_code_sent_at',
            'email',
            'username',
            'first_name',
            'last_name'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in field_names:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        else:
            print("✅ All required fields exist in CustomUser model")
            return True
            
    except Exception as e:
        print(f"❌ Error checking model fields: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Django registration fix...")
    print("=" * 50)
    
    # Test 1: Check model fields
    fields_ok = test_model_fields()
    
    # Test 2: Test user creation
    creation_ok = test_user_creation()
    
    print("=" * 50)
    if fields_ok and creation_ok:
        print("🎉 All tests passed! Registration should work now.")
    else:
        print("💥 Some tests failed. Check the errors above.")
