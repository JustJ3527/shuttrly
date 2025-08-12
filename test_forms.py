#!/usr/bin/env python3
"""
Simple test script to verify forms can be imported correctly.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")

    try:
        # Test Django setup
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shuttrly.settings")

        # Test basic imports
        import django

        print("✅ Django imported successfully")

        # Setup Django
        django.setup()
        print("✅ Django setup completed")

        # Test form imports
        from users.forms import (
            EditProfileStep1Form,
            EditProfileStep2Form,
            EditProfileStep3Form,
            EditProfileStep4Form,
            EditProfileStep5Form,
        )

        print("✅ All profile editing forms imported successfully")

        # Test form creation
        form1 = EditProfileStep1Form()
        form2 = EditProfileStep2Form()
        form3 = EditProfileStep3Form()
        form4 = EditProfileStep4Form()
        form5 = EditProfileStep5Form()
        print("✅ All forms created successfully")

        print("\n🎉 All tests passed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    if not success:
        sys.exit(1)
    print("\n✅ Forms are ready to use!")
