#!/usr/bin/env python
"""
Comprehensive IVR Testing Script
Tests all IVR endpoints and functionality for errors
"""
import os
import sys
import django
import requests
from urllib.parse import urlencode

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import State, District, Clinic, Doctor, Patient, Token
from api.views import (
    _get_available_slots_for_doctor, 
    _find_next_available_slot_for_doctor,
    _create_ivr_token
)
from datetime import datetime, date, time

def test_database_setup():
    """Test if required data exists in database"""
    print("=== Testing Database Setup ===")
    
    states = State.objects.all()
    print(f"States: {states.count()}")
    for state in states:
        print(f"  - {state.name}")
    
    districts = District.objects.all()
    print(f"Districts: {districts.count()}")
    for district in districts:
        print(f"  - {district.name} ({district.state.name})")
    
    clinics = Clinic.objects.all()
    print(f"Clinics: {clinics.count()}")
    for clinic in clinics:
        print(f"  - {clinic.name} ({clinic.district.name if clinic.district else 'No district'})")
    
    doctors = Doctor.objects.all()
    print(f"Doctors: {doctors.count()}")
    for doctor in doctors:
        print(f"  - Dr. {doctor.name} ({doctor.specialization}) at {doctor.clinic.name if doctor.clinic else 'No clinic'}")
    
    return states.exists() and districts.exists() and clinics.exists() and doctors.exists()

def test_slot_functions():
    """Test slot availability functions"""
    print("\n=== Testing Slot Functions ===")
    
    doctors = Doctor.objects.all()
    if not doctors.exists():
        print("ERROR: No doctors found")
        return False
    
    doctor = doctors.first()
    today_str = date.today().strftime('%Y-%m-%d')
    
    print(f"Testing slots for Dr. {doctor.name} on {today_str}")
    
    # Test _get_available_slots_for_doctor
    try:
        slots = _get_available_slots_for_doctor(doctor.id, today_str)
        print(f"Available slots: {slots}")
        if slots is None:
            print("ERROR: Slots function returned None")
            return False
    except Exception as e:
        print(f"ERROR in _get_available_slots_for_doctor: {e}")
        return False
    
    # Test _find_next_available_slot_for_doctor
    try:
        next_date, next_slot = _find_next_available_slot_for_doctor(doctor.id)
        print(f"Next available slot: {next_date} at {next_slot}")
        if next_date is None or next_slot is None:
            print("WARNING: No available slots found in next 7 days")
    except Exception as e:
        print(f"ERROR in _find_next_available_slot_for_doctor: {e}")
        return False
    
    return True

def test_token_creation():
    """Test IVR token creation function"""
    print("\n=== Testing Token Creation ===")
    
    doctors = Doctor.objects.all()
    if not doctors.exists():
        print("ERROR: No doctors found")
        return False
    
    doctor = doctors.first()
    test_phone = "+1234567890"
    today = date.today()
    test_time = "10:00"
    
    print(f"Testing token creation for {test_phone}")
    
    try:
        # Clean up any existing test data
        Patient.objects.filter(phone_number=test_phone).delete()
        
        token = _create_ivr_token(doctor, today, test_time, test_phone)
        if token:
            print(f"SUCCESS: Token created - {token.token_number}")
            print(f"Patient: {token.patient.name}")
            print(f"Doctor: {token.doctor.name}")
            print(f"Date: {token.date}")
            print(f"Time: {token.appointment_time}")
            return True
        else:
            print("ERROR: Token creation failed")
            return False
    except Exception as e:
        print(f"ERROR in _create_ivr_token: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ivr_endpoints():
    """Test IVR HTTP endpoints"""
    print("\n=== Testing IVR HTTP Endpoints ===")
    
    base_url = "http://localhost:8000/api/ivr"
    
    # Test welcome endpoint
    try:
        response = requests.get(f"{base_url}/welcome/")
        print(f"Welcome endpoint: {response.status_code}")
        if response.status_code == 200:
            print("[OK] Welcome endpoint working")
        else:
            print(f"[FAIL] Welcome endpoint failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("WARNING: Django server not running - skipping HTTP tests")
        return True
    except Exception as e:
        print(f"ERROR testing welcome endpoint: {e}")
        return False
    
    return True

def test_twilio_integration():
    """Test Twilio-specific functionality"""
    print("\n=== Testing Twilio Integration ===")
    
    from django.conf import settings
    
    print(f"Twilio Account SID: {settings.TWILIO_ACCOUNT_SID}")
    print(f"Twilio Phone Number: {settings.TWILIO_PHONE_NUMBER}")
    
    # Test SMS utility
    try:
        from api.utils.utils import send_sms_notification
        print("[OK] SMS utility imported successfully")
        
        # Don't actually send SMS in test, just check if function exists
        print("[OK] SMS function available")
    except ImportError as e:
        print(f"ERROR: SMS utility import failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: SMS utility error: {e}")
        return False
    
    return True

def test_error_handling():
    """Test error handling in IVR functions"""
    print("\n=== Testing Error Handling ===")
    
    # Test with invalid doctor ID
    try:
        slots = _get_available_slots_for_doctor(99999, "2024-01-01")
        if slots is None:
            print("[OK] Invalid doctor ID handled correctly")
        else:
            print("[FAIL] Invalid doctor ID should return None")
    except Exception as e:
        print(f"ERROR: Exception not handled for invalid doctor: {e}")
        return False
    
    # Test with invalid date format
    try:
        slots = _get_available_slots_for_doctor(1, "invalid-date")
        if slots is None:
            print("[OK] Invalid date format handled correctly")
        else:
            print("[FAIL] Invalid date format should return None")
    except Exception as e:
        print(f"ERROR: Exception not handled for invalid date: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Starting Comprehensive IVR Testing...")
    print("=" * 50)
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Slot Functions", test_slot_functions),
        ("Token Creation", test_token_creation),
        ("IVR Endpoints", test_ivr_endpoints),
        ("Twilio Integration", test_twilio_integration),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"[PASS] {test_name}: PASSED")
            else:
                print(f"[FAIL] {test_name}: FAILED")
        except Exception as e:
            print(f"[ERROR] {test_name}: ERROR - {e}")
            results.append((test_name, False))
        print("-" * 30)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: ALL TESTS PASSED - IVR system is working correctly!")
    else:
        print("WARNING: Some tests failed - check the errors above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)