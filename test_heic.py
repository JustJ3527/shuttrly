#!/usr/bin/env python
"""
Test script to verify HEIC support and thumbnail generation
"""
import os
import sys
import django
from PIL import Image

# Setup Django
sys.path.append('/Users/julesantoine/Documents/ShuttrlyMainFolder/shuttrly')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
django.setup()

# Import pillow-heif for HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    print("✅ pillow-heif registered successfully")
except ImportError as e:
    print(f"❌ Failed to import pillow-heif: {e}")
    sys.exit(1)

def test_heic_support():
    """Test if PIL can open HEIC files"""
    print("\n🔍 Testing HEIC support...")
    
    # Test if PIL recognizes HEIC format
    try:
        from PIL import Image
        print(f"✅ PIL version: {Image.__version__}")
        
        # Check if HEIC is in supported formats
        if 'HEIF' in Image.registered_extensions():
            print("✅ HEIF format is registered in PIL")
        else:
            print("❌ HEIF format not found in PIL registered extensions")
            
        # List all registered extensions
        print(f"📋 Registered extensions: {list(Image.registered_extensions().keys())}")
        
    except Exception as e:
        print(f"❌ Error testing PIL: {e}")

def test_heic_file_processing():
    """Test processing a HEIC file if one exists"""
    print("\n🔍 Testing HEIC file processing...")
    
    # Look for HEIC files in the media directory
    media_path = "/Users/julesantoine/Documents/ShuttrlyMainFolder/shuttrly/media/photos"
    
    if os.path.exists(media_path):
        for root, dirs, files in os.walk(media_path):
            for file in files:
                if file.lower().endswith(('.heic', '.heif')):
                    file_path = os.path.join(root, file)
                    print(f"📁 Found HEIC file: {file_path}")
                    
                    try:
                        # Try to open with PIL
                        with Image.open(file_path) as img:
                            print(f"✅ Successfully opened HEIC file")
                            print(f"   - Format: {img.format}")
                            print(f"   - Mode: {img.mode}")
                            print(f"   - Size: {img.size}")
                            
                            # Test thumbnail generation
                            img_copy = img.copy()
                            img_copy.thumbnail((450, 450), Image.Resampling.LANCZOS)
                            print(f"✅ Thumbnail generation successful: {img_copy.size}")
                            
                    except Exception as e:
                        print(f"❌ Error processing HEIC file: {e}")
                    
                    return  # Test only the first HEIC file found
    
    print("ℹ️  No HEIC files found in media directory for testing")

if __name__ == "__main__":
    print("🧪 HEIC Support Test")
    print("=" * 50)
    
    test_heic_support()
    test_heic_file_processing()
    
    print("\n✅ Test completed!")
