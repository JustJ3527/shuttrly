#!/usr/bin/env python3
"""
Test script for hashtag functionality in Photo model
Run this script to test hashtag operations
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
django.setup()

from photos.models import Photo, Collection
from django.contrib.auth import get_user_model

User = get_user_model()

def test_hashtag_functionality():
    """Test hashtag functionality for photos"""
    print("=== Testing Hashtag Functionality ===\n")
    
    # Get a test user (first user in database)
    try:
        user = User.objects.first()
        if not user:
            print("No users found in database. Please create a user first.")
            return
        print(f"Testing with user: {user.username}")
    except Exception as e:
        print(f"Error getting user: {e}")
        return
    
    # Get a test photo
    try:
        photo = Photo.objects.filter(user=user).first()
        if not photo:
            print("No photos found for this user. Please upload a photo first.")
            return
        print(f"Testing with photo: {photo.title or 'Untitled'} (ID: {photo.id})")
    except Exception as e:
        print(f"Error getting photo: {e}")
        return
    
    print(f"\nCurrent tags: '{photo.tags}'")
    print(f"Current tags list: {photo.get_tags_list()}")
    
    # Test adding tags
    print("\n--- Testing tag addition ---")
    
    # Add some test tags
    test_tags = ['landscape', 'nature', 'sunset']
    for tag in test_tags:
        photo.add_tag(tag)
        print(f"Added tag '{tag}' -> Tags: '{photo.tags}'")
    
    # Test getting tags list
    print(f"\nTags after addition: {photo.get_tags_list()}")
    
    # Test checking if photo has specific tags
    print("\n--- Testing tag checking ---")
    for tag in test_tags:
        has_tag = photo.has_tag(tag)
        print(f"Photo has tag '{tag}': {has_tag}")
    
    # Test removing tags
    print("\n--- Testing tag removal ---")
    photo.remove_tag('nature')
    print(f"Removed 'nature' -> Tags: '{photo.tags}'")
    print(f"Tags list after removal: {photo.get_tags_list()}")
    
    # Test setting tags from list
    print("\n--- Testing set_tags_from_list ---")
    new_tags = ['city', 'architecture', 'modern']
    photo.set_tags_from_list(new_tags)
    print(f"Set tags from list {new_tags} -> Tags: '{photo.tags}'")
    print(f"Tags list: {photo.get_tags_list()}")
    
    # Test with existing hashtags
    print("\n--- Testing with existing hashtags ---")
    photo.tags = "#existing #test #hashtags"
    print(f"Set tags with existing hashtags: '{photo.tags}'")
    print(f"Tags list: {photo.get_tags_list()}")
    
    # Test adding tag that already has #
    print("\n--- Testing adding tag with # ---")
    photo.add_tag('#newtag')
    print(f"Added '#newtag' -> Tags: '{photo.tags}'")
    
    # Test adding tag without #
    print("\n--- Testing adding tag without # ---")
    photo.add_tag('anothertag')
    print(f"Added 'anothertag' -> Tags: '{photo.tags}'")
    
    # Final state
    print(f"\n--- Final State ---")
    print(f"Final tags string: '{photo.tags}'")
    print(f"Final tags list: {photo.get_tags_list()}")
    
    # Save the photo to persist changes
    try:
        photo.save()
        print("\n✅ Photo saved successfully with updated tags!")
    except Exception as e:
        print(f"\n❌ Error saving photo: {e}")
    
    print("\n=== Hashtag Testing Complete ===")

if __name__ == '__main__':
    test_hashtag_functionality()
