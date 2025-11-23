#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.ai_client import summarize_text, get_model_name, is_model_loaded

def test_ai_summary():
    print("Testing AI Summary System...")
    print(f"Model loaded: {is_model_loaded()}")
    print(f"Model name: {get_model_name()}")
    
    # Test text
    test_text = """
    Patient: John Doe
    Date: 2025-11-24
    Chief Complaint: Fever and headache for 3 days
    History: Patient reports high fever (102°F) with severe headache. No nausea or vomiting.
    Examination: Temperature 102°F, BP 120/80, Pulse 90/min
    Diagnosis: Viral fever
    Treatment: Prescribed Paracetamol 500mg TID for 5 days
    Advice: Rest, plenty of fluids, follow up if symptoms worsen
    """
    
    try:
        result = summarize_text(test_text, max_length=200, min_length=50)
        print(f"Summary result: {result}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_summary()
    print(f"Test {'PASSED' if success else 'FAILED'}")