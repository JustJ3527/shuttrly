#!/usr/bin/env python
"""
Test script for the new recommendation system.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.tasks import (
    build_user_recommendations_for_user, 
    get_user_recommendations_for_display,
    trigger_recommendation_update_after_relationship_change
)
import time

User = get_user_model()

def test_recommendation_system():
    """Test the complete recommendation system."""
    print("🧪 Testing Recommendation System")
    print("=" * 50)
    
    # Get a test user
    user = User.objects.filter(is_active=True, is_anonymized=False).first()
    if not user:
        print("❌ No active users found")
        return
    
    print(f"👤 Testing with user: {user.username} (ID: {user.id})")
    
    # Test 1: Generate top 30 recommendations
    print("\n1️⃣ Generating top 30 recommendations...")
    result = build_user_recommendations_for_user(user.id, top_k=30)
    if result.get('success'):
        print(f"✅ Generated {result.get('recommendations_count', 0)} recommendations")
    else:
        print(f"❌ Failed: {result.get('error')}")
        return
    
    # Test 2: Get 4 recommendations with rotation
    print("\n2️⃣ Getting 4 recommendations with rotation...")
    rotation_key = int(time.time())
    result = get_user_recommendations_for_display(user.id, limit=4, rotation_key=rotation_key)
    
    if result.get('status') == 'success':
        recommendations = result.get('recommendations', [])
        print(f"✅ Got {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['username']} (score: {rec['score']:.4f})")
    else:
        print(f"❌ Failed: {result.get('message')}")
        return
    
    # Test 3: Test rotation with different key
    print("\n3️⃣ Testing rotation with different key...")
    rotation_key2 = int(time.time()) + 1000
    result2 = get_user_recommendations_for_display(user.id, limit=4, rotation_key=rotation_key2)
    
    if result2.get('status') == 'success':
        recommendations2 = result2.get('recommendations', [])
        print(f"✅ Got {len(recommendations2)} different recommendations:")
        for i, rec in enumerate(recommendations2, 1):
            print(f"   {i}. {rec['username']} (score: {rec['score']:.4f})")
        
        # Check if recommendations are different
        usernames1 = {rec['username'] for rec in recommendations}
        usernames2 = {rec['username'] for rec in recommendations2}
        if usernames1 != usernames2:
            print("✅ Rotation is working - different recommendations shown")
        else:
            print("⚠️ Rotation might not be working - same recommendations shown")
    else:
        print(f"❌ Failed: {result2.get('message')}")
    
    # Test 4: Test follow trigger
    print("\n4️⃣ Testing follow trigger...")
    try:
        # This would normally be called after a follow/unfollow action
        task = trigger_recommendation_update_after_relationship_change.delay(
            user.id, 
            "test_follow_action"
        )
        print(f"✅ Triggered background update (Task ID: {task.id})")
    except Exception as e:
        print(f"❌ Failed to trigger update: {e}")
    
    print("\n🎉 Recommendation system test completed!")

if __name__ == '__main__':
    test_recommendation_system()
