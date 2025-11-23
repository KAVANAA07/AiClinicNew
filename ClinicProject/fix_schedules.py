#!/usr/bin/env python
"""
Fix Django-Q schedules and test IVR system
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django_q.models import Schedule
from api.models import State, District, Clinic, Doctor

def fix_schedules():
    """Clean up and fix Django-Q schedules"""
    print("=== Fixing Django-Q Schedules ===")
    
    # Delete all existing schedules to start fresh
    old_schedules = Schedule.objects.all()
    count = old_schedules.count()
    if count > 0:
        old_schedules.delete()
        print(f"[OK] Deleted {count} old schedules")
    
    # Create the correct schedule
    try:
        Schedule.objects.create(
            name='check_missed_appointments',
            func='api.tasks.check_and_cancel_missed_slots',
            schedule_type=Schedule.MINUTES,
            minutes=5,
            repeats=-1  # Run indefinitely
        )
        print("[OK] Created new schedule: check_missed_appointments (every 5 minutes)")
    except Exception as e:
        print(f"[ERROR] Failed to create schedule: {e}")
    
    # List current schedules
    schedules = Schedule.objects.all()
    print(f"\nCurrent schedules ({schedules.count()}):")
    for schedule in schedules:
        print(f"  - {schedule.name}: {schedule.func} (every {schedule.minutes} min)")

def test_basic_setup():
    """Test basic system setup"""
    print("\n=== Testing Basic Setup ===")
    
    # Check database
    states = State.objects.count()
    districts = District.objects.count()
    clinics = Clinic.objects.count()
    doctors = Doctor.objects.count()
    
    print(f"Database counts:")
    print(f"  States: {states}")
    print(f"  Districts: {districts}")
    print(f"  Clinics: {clinics}")
    print(f"  Doctors: {doctors}")
    
    if states == 0:
        print("\n[WARNING] No states found!")
        print("  IVR system needs at least 1 state, district, clinic, and doctor")
        print("  Run: python setup_test_data.py")
        return False
    
    if doctors == 0:
        print("\n[WARNING] No doctors found!")
        print("  IVR system needs at least 1 doctor to book appointments")
        print("  Run: python setup_test_data.py")
        return False
    
    print("[OK] Basic setup looks good")
    return True

def test_ivr_function():
    """Test the IVR welcome function directly"""
    print("\n=== Testing IVR Function ===")
    
    try:
        from api.views import ivr_welcome
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/ivr/welcome/', {
            'From': '+1234567890',
            'CallSid': 'test_call_123'
        })
        
        response = ivr_welcome(request)
        print(f"IVR Welcome Response Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if '<Response>' in content and 'Welcome to ClinicFlow' in content:
                print("[OK] IVR Welcome function is working correctly")
                return True
            else:
                print("[WARNING] IVR response doesn't contain expected content")
                print(f"Response: {content[:200]}...")
        else:
            print(f"[ERROR] IVR Welcome failed with status {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Error testing IVR function: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == '__main__':
    fix_schedules()
    
    if test_basic_setup():
        test_ivr_function()
    
    print("\n=== Next Steps ===")
    print("1. Restart Django-Q cluster: python manage.py qcluster")
    print("2. Start Django server: python manage.py runserver")
    print("3. Test IVR by calling your Twilio number")
    print("4. Watch Django terminal for login/IVR log messages")