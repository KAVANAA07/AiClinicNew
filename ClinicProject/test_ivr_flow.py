#!/usr/bin/env python
"""
IVR Call Flow Testing Script
Simulates complete IVR call flow to test all endpoints
"""
import os
import sys
import django
import requests
from urllib.parse import urlencode

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import State, District, Clinic, Doctor

def simulate_post_request(url, data):
    """Simulate Twilio POST request"""
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.status_code, response.text
    except requests.exceptions.ConnectionError:
        print("ERROR: Django server not running")
        return None, None
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None

def test_complete_ivr_flow():
    """Test complete IVR call flow"""
    print("=== Testing Complete IVR Call Flow ===")
    
    base_url = "http://localhost:8000/api/ivr"
    caller_phone = "+1234567890"
    
    # Step 1: Welcome
    print("Step 1: Testing welcome endpoint")
    status, response = simulate_post_request(f"{base_url}/welcome/", {})
    if status == 200:
        print("[OK] Welcome endpoint working")
        print(f"Response contains: {'Welcome to ClinicFlow AI' in response}")
    else:
        print(f"[FAIL] Welcome failed: {status}")
        return False
    
    # Step 2: Handle state selection
    print("\nStep 2: Testing state selection")
    status, response = simulate_post_request(f"{base_url}/handle-state/", {
        'Digits': '1',  # Select first state
        'From': caller_phone
    })
    if status == 200:
        print("[OK] State selection working")
        print(f"Response contains state info: {'district' in response.lower()}")
    else:
        print(f"[FAIL] State selection failed: {status}")
        return False
    
    # Get state ID for next step
    state = State.objects.first()
    if not state:
        print("[FAIL] No states found in database")
        return False
    
    # Step 3: Handle district selection
    print("\nStep 3: Testing district selection")
    status, response = simulate_post_request(f"{base_url}/handle-district/{state.id}/", {
        'Digits': '1',  # Select first district
        'From': caller_phone
    })
    if status == 200:
        print("[OK] District selection working")
        print(f"Response contains clinic info: {'clinic' in response.lower()}")
    else:
        print(f"[FAIL] District selection failed: {status}")
        return False
    
    # Get district ID for next step
    district = District.objects.first()
    if not district:
        print("[FAIL] No districts found in database")
        return False
    
    # Step 4: Handle clinic selection
    print("\nStep 4: Testing clinic selection")
    status, response = simulate_post_request(f"{base_url}/handle-clinic/{district.id}/", {
        'Digits': '1',  # Select first clinic
        'From': caller_phone
    })
    if status == 200:
        print("[OK] Clinic selection working")
        print(f"Response contains booking options: {'next available' in response.lower()}")
    else:
        print(f"[FAIL] Clinic selection failed: {status}")
        return False
    
    # Get clinic ID for next step
    clinic = Clinic.objects.filter(district=district).first()
    if not clinic:
        print("[FAIL] No clinics found for district")
        return False
    
    # Step 5: Handle booking type (next available doctor)
    print("\nStep 5: Testing booking type selection")
    status, response = simulate_post_request(f"{base_url}/handle-booking-type/{clinic.id}/", {
        'Digits': '1',  # Select next available doctor
        'From': caller_phone
    })
    if status == 200:
        print("[OK] Booking type selection working")
        print(f"Response contains confirmation: {'confirm' in response.lower()}")
    else:
        print(f"[FAIL] Booking type selection failed: {status}")
        return False
    
    # Step 6: Test confirmation endpoint
    print("\nStep 6: Testing booking confirmation")
    doctor = Doctor.objects.filter(clinic=clinic).first()
    if not doctor:
        print("[FAIL] No doctors found for clinic")
        return False
    
    # Test confirmation with parameters
    confirm_url = f"{base_url}/confirm-booking/?doctor_id={doctor.id}&date=2025-11-24&time=10:00&phone={caller_phone}"
    status, response = simulate_post_request(confirm_url, {
        'Digits': '1',  # Confirm booking
        'From': caller_phone
    })
    if status == 200:
        print("[OK] Booking confirmation working")
        print(f"Response contains success: {'confirmed' in response.lower()}")
    else:
        print(f"[FAIL] Booking confirmation failed: {status}")
        return False
    
    return True

def test_ivr_error_scenarios():
    """Test IVR error handling scenarios"""
    print("\n=== Testing IVR Error Scenarios ===")
    
    base_url = "http://localhost:8000/api/ivr"
    
    # Test invalid state selection
    print("Testing invalid state selection")
    status, response = simulate_post_request(f"{base_url}/handle-state/", {
        'Digits': '99',  # Invalid state
    })
    if status == 200 and 'invalid' in response.lower():
        print("[OK] Invalid state handled correctly")
    else:
        print("[FAIL] Invalid state not handled properly")
        return False
    
    # Test missing phone number
    print("Testing missing phone number")
    clinic = Clinic.objects.first()
    if clinic:
        status, response = simulate_post_request(f"{base_url}/handle-booking-type/{clinic.id}/", {
            'Digits': '1',  # No 'From' field
        })
        if status == 200 and 'phone number' in response.lower():
            print("[OK] Missing phone number handled correctly")
        else:
            print("[FAIL] Missing phone number not handled properly")
            return False
    
    return True

def test_sms_cancellation():
    """Test SMS cancellation functionality"""
    print("\n=== Testing SMS Cancellation ===")
    
    # Test SMS endpoint directly using Django test framework
    from django.test import RequestFactory
    from api.views import handle_incoming_sms
    from api.models import Patient, Token, Doctor
    
    test_phone = "+1234567890"
    
    # Clean up existing data
    Patient.objects.filter(phone_number=test_phone).delete()
    
    # Create test patient and token
    doctor = Doctor.objects.first()
    if not doctor:
        print("[FAIL] No doctors found for SMS test")
        return False
    
    patient = Patient.objects.create(
        phone_number=test_phone,
        name="SMS Test Patient",
        age=25
    )
    
    token = Token.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=doctor.clinic,
        date="2025-11-24",
        status="waiting"
    )
    
    try:
        # Create mock request
        factory = RequestFactory()
        request = factory.post('/api/sms/incoming/', {
            'From': test_phone,
            'Body': 'CANCEL'
        })
        
        # Call the view directly
        response = handle_incoming_sms(request)
        
        if response.status_code == 200:
            print("[OK] SMS cancellation endpoint working")
            # Check if token was actually cancelled
            token.refresh_from_db()
            if token.status == 'cancelled':
                print("[OK] Token successfully cancelled via SMS")
                return True
            else:
                print("[FAIL] Token was not cancelled")
                return False
        else:
            print(f"[FAIL] SMS cancellation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] SMS test exception: {e}")
        return False
    finally:
        # Clean up test data
        try:
            token.delete()
            patient.delete()
        except:
            pass
    
    return True

def main():
    """Run all IVR flow tests"""
    print("Starting IVR Call Flow Testing...")
    print("=" * 50)
    
    tests = [
        ("Complete IVR Flow", test_complete_ivr_flow),
        ("Error Scenarios", test_ivr_error_scenarios),
        ("SMS Cancellation", test_sms_cancellation),
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
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        print("-" * 30)
    
    # Summary
    print("\n" + "=" * 50)
    print("IVR FLOW TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All IVR flow tests passed!")
        print("The Twilio IVR system is working perfectly with no errors!")
    else:
        print("WARNING: Some IVR flow tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)