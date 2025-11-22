#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.ai_client import summarize_text, get_model_name, is_model_loaded

print("=== AI Client Test ===")
print(f"Model loaded: {is_model_loaded()}")
print(f"Model name: {get_model_name()}")

try:
    test_text = "Patient has fever and headache. Doctor prescribed medication for symptoms."
    print(f"Testing with: {test_text}")
    result = summarize_text(test_text)
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()