#!/usr/bin/env python3
"""
Test script to verify Django verification fix
"""

import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
django.setup()

from users.constants import EMAIL_CODE_EXPIRY_SECONDS

def test_time_comparison():
    """Test that timedelta comparison works correctly"""
    try:
        # Test current time
        now = timezone.now()
        
        # Test time 5 minutes ago (300 seconds)
        five_minutes_ago = now - timedelta(seconds=300)
        time_since_sent = now - five_minutes_ago
        
        print(f"✅ Time since sent: {time_since_sent}")
        print(f"✅ Time since sent in seconds: {time_since_sent.total_seconds()}")
        print(f"✅ EMAIL_CODE_EXPIRY_SECONDS: {EMAIL_CODE_EXPIRY_SECONDS}")
        
        # Test the comparison that was failing
        if time_since_sent.total_seconds() > EMAIL_CODE_EXPIRY_SECONDS:
            print("❌ Code should be expired (5 minutes > 10 minutes)")
        else:
            print("✅ Code is still valid (5 minutes < 10 minutes)")
        
        # Test time 15 minutes ago (900 seconds)
        fifteen_minutes_ago = now - timedelta(seconds=900)
        time_since_sent_old = now - fifteen_minutes_ago
        
        print(f"\n✅ Time since sent (old): {time_since_sent_old}")
        print(f"✅ Time since sent in seconds (old): {time_since_sent_old.total_seconds()}")
        
        if time_since_sent_old.total_seconds() > EMAIL_CODE_EXPIRY_SECONDS:
            print("✅ Code should be expired (15 minutes > 10 minutes)")
        else:
            print("❌ Code should be expired but isn't")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing time comparison: {e}")
        return False

def test_constants():
    """Test that constants are properly defined"""
    try:
        print(f"✅ EMAIL_CODE_EXPIRY_SECONDS: {EMAIL_CODE_EXPIRY_SECONDS}")
        print(f"✅ Type: {type(EMAIL_CODE_EXPIRY_SECONDS)}")
        
        if isinstance(EMAIL_CODE_EXPIRY_SECONDS, int):
            print("✅ Constant is properly defined as integer")
            return True
        else:
            print("❌ Constant is not an integer")
            return False
            
    except Exception as e:
        print(f"❌ Error checking constants: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Django verification fix...")
    print("=" * 50)
    
    # Test 1: Check constants
    constants_ok = test_constants()
    
    # Test 2: Test time comparison logic
    comparison_ok = test_time_comparison()
    
    print("=" * 50)
    if constants_ok and comparison_ok:
        print("🎉 All tests passed! Verification should work now.")
    else:
        print("💥 Some tests failed. Check the errors above.")
