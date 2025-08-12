#!/usr/bin/env python3
"""
Test script to verify step 2 logic for profile editing.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_step2_logic():
    """Test the step 2 verification logic."""
    print("🧪 Testing Step 2 Logic...")

    # Simulate the logic from the view
    EMAIL_CODE_RESEND_DELAY_SECONDS = 120  # 2 minutes

    # Test case 1: Code just sent (should not allow resend)
    print("\n📧 Test 1: Code just sent")
    code_sent_at = datetime.now().isoformat()
    print(f"Code sent at: {code_sent_at}")

    # Simulate the logic
    sent_time = datetime.fromisoformat(code_sent_at)
    delta = datetime.now() - sent_time
    time_until_resend = max(0, EMAIL_CODE_RESEND_DELAY_SECONDS - delta.total_seconds())
    can_resend = time_until_resend <= 0

    print(f"Time since sent: {delta.total_seconds():.1f} seconds")
    print(f"Time until resend: {time_until_resend:.1f} seconds")
    print(f"Can resend: {can_resend}")

    # Test case 2: Code sent 3 minutes ago (should allow resend)
    print("\n📧 Test 2: Code sent 3 minutes ago")
    code_sent_at_old = (datetime.now() - timedelta(minutes=3)).isoformat()
    print(f"Code sent at: {code_sent_at_old}")

    sent_time_old = datetime.fromisoformat(code_sent_at_old)
    delta_old = datetime.now() - sent_time_old
    time_until_resend_old = max(
        0, EMAIL_CODE_RESEND_DELAY_SECONDS - delta_old.total_seconds()
    )
    can_resend_old = time_until_resend_old <= 0

    print(f"Time since sent: {delta_old.total_seconds():.1f} seconds")
    print(f"Time until resend: {time_until_resend_old:.1f} seconds")
    print(f"Can resend: {can_resend_old}")

    # Test case 3: Edge case - exactly 2 minutes
    print("\n📧 Test 3: Edge case - exactly 2 minutes")
    code_sent_at_edge = (datetime.now() - timedelta(minutes=2)).isoformat()
    print(f"Code sent at: {code_sent_at_edge}")

    sent_time_edge = datetime.fromisoformat(code_sent_at_edge)
    delta_edge = datetime.now() - sent_time_edge
    time_until_resend_edge = max(
        0, EMAIL_CODE_RESEND_DELAY_SECONDS - delta_edge.total_seconds()
    )
    can_resend_edge = time_until_resend_edge <= 0

    print(f"Time since sent: {delta_edge.total_seconds():.1f} seconds")
    print(f"Time until resend: {time_until_resend_edge:.1f} seconds")
    print(f"Can resend: {can_resend_edge}")

    print("\n🎉 Step 2 logic test completed!")
    return True


if __name__ == "__main__":
    test_step2_logic()
