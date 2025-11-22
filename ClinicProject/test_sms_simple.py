#!/usr/bin/env python
"""
Simple SMS endpoint test
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Patient, Token
from api.views import handle_incoming_sms
from django.test import RequestFactory
from django.http import HttpRequest

def test_sms_endpoint():
    """Test SMS endpoint directly"""
    print("=== Testing SMS Endpoint ===")
    
    # Create a test patient with a token
    test_phone = "+1234567890"
    
    # Clean up existing data
    Patient.objects.filter(phone_number=test_phone).delete()
    
    # Create test patient and token
    from api.models import Doctor, Clinic
    doctor = Doctor.objects.first()
    if not doctor:
        print("ERROR: No doctors found")
        return False
    
    patient = Patient.objects.create(
        phone_number=test_phone,
        name="Test Patient",
        age=30
    )
    
    token = Token.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=doctor.clinic,
        date="2025-11-24",
        status="waiting"
    )
    
    print(f"Created test patient: {patient.name}")
    print(f"Created test token: {token.id}")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.post('/api/sms/incoming/', {
        'From': test_phone,
        'Body': 'CANCEL'
    })
    
    try:
        response = handle_incoming_sms(request)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        # Check if token was cancelled
        token.refresh_from_db()
        print(f"Token status after SMS: {token.status}")
        
        if token.status == 'cancelled':
            print("[OK] SMS cancellation worked correctly")
            return True
        else:
            print("[FAIL] Token was not cancelled")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        token.delete()
        patient.delete()

if __name__ == "__main__":
    success = test_sms_endpoint()
    print(f"\nSMS Test Result: {'PASSED' if success else 'FAILED'}")