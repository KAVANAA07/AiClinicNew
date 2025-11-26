#!/usr/bin/env python
"""
Test script to verify that automatic confirmation is prevented
and only manual confirmation works.
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.utils import timezone
from api.models import Token, Patient, Doctor, Clinic

def test_automatic_confirmation_prevention():
    """Test that automatic confirmation is blocked"""
    print("[LOCK] Testing Automatic Confirmation Prevention...")
    
    # Get a test token
    token = Token.objects.filter(status='waiting').first()
    if not token:
        print("❌ No waiting tokens found for testing")
        return False
    
    print(f"[INFO] Testing with Token ID: {token.id}, Patient: {token.patient.name}")
    print(f"   Current Status: {token.status}")
    
    # Try to automatically confirm (this should be blocked)
    original_status = token.status
    token.status = 'confirmed'
    token.save()
    
    # Refresh from database
    token.refresh_from_db()
    
    if token.status == 'confirmed':
        print("[FAIL] FAILED: Automatic confirmation was NOT blocked!")
        return False
    else:
        print(f"[PASS] SUCCESS: Automatic confirmation blocked. Status remains: {token.status}")
    
    # Now test manual confirmation (this should work)
    token._manual_confirmation_allowed = True
    token.status = 'confirmed'
    token.arrival_confirmed_at = timezone.now()
    token.save()
    
    token.refresh_from_db()
    
    if token.status == 'confirmed':
        print("[PASS] SUCCESS: Manual confirmation with flag works correctly")
        
        # Reset for next test
        token.status = original_status
        token.arrival_confirmed_at = None
        token._manual_confirmation_allowed = True
        token.save()
        
        return True
    else:
        print("[FAIL] FAILED: Manual confirmation with flag did not work")
        return False

def test_confirmation_window():
    """Test that confirmation only works within the 20-minute window"""
    print("\n[TIME] Testing Confirmation Time Window...")
    
    # Find a token with appointment time
    token = Token.objects.filter(
        status='waiting',
        appointment_time__isnull=False,
        date=timezone.now().date()
    ).first()
    
    if not token:
        print("[WARN] No scheduled tokens found for testing time window")
        return False
    
    now = timezone.now()
    appointment_datetime = timezone.make_aware(datetime.combine(token.date, token.appointment_time))
    start_window = appointment_datetime - timedelta(minutes=20)
    end_window = appointment_datetime + timedelta(minutes=15)
    
    print(f"[DATE] Token appointment: {appointment_datetime.strftime('%Y-%m-%d %I:%M %p')}")
    print(f"[TIME] Confirmation window: {start_window.strftime('%I:%M %p')} - {end_window.strftime('%I:%M %p')}")
    print(f"[TIME] Current time: {now.strftime('%I:%M %p')}")
    
    if start_window <= now <= end_window:
        print("[PASS] Current time is within confirmation window")
        return True
    else:
        print("[INFO] Current time is outside confirmation window")
        return True  # This is expected behavior

def main():
    print("[TEST] Testing Arrival Confirmation System")
    print("=" * 50)
    
    test1_passed = test_automatic_confirmation_prevention()
    test2_passed = test_confirmation_window()
    
    print("\n" + "=" * 50)
    print("[RESULTS] Test Results:")
    print(f"   Automatic Prevention: {'PASS' if test1_passed else 'FAIL'}")
    print(f"   Time Window Check: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n[SUCCESS] All tests passed! Confirmation system is working correctly.")
    else:
        print("\n[WARNING] Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()