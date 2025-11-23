#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.conf import settings
from api.ai_client import is_model_loaded, get_model_name, load_local_model

def test_ai_client_debug():
    print("=== AI Client Debug ===")
    print(f"AI_BACKEND setting: {getattr(settings, 'AI_BACKEND', 'NOT SET')}")
    print(f"Model loaded: {is_model_loaded()}")
    print(f"Model name: {get_model_name()}")
    
    # Try to load local model
    print("\nTrying to load local model...")
    try:
        success = load_local_model()
        print(f"Load result: {success}")
        print(f"Model loaded after load: {is_model_loaded()}")
        print(f"Model name after load: {get_model_name()}")
    except Exception as e:
        print(f"Error loading model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_client_debug()