#!/usr/bin/env python
"""
Test simple SMS without emojis
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.utils.utils import send_sms_notification

def test_simple_sms():
    phone = "+918217612080"  # Your phone number
    message = "Test SMS from MedQ clinic system. This is a simple test message without emojis."
    
    try:
        result = send_sms_notification(phone, message)
        print(f"SMS sent successfully: {result}")
    except Exception as e:
        print(f"SMS failed: {e}")

if __name__ == "__main__":
    test_simple_sms()