#!/usr/bin/env python
import os
import django
from django.conf import settings
from datetime import datetime, time, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Patient, Doctor, Clinic
from api.tasks import check_and_cancel_missed_slots

def create_test_token():
    print("=== Creating Test Token with Past Appointment Time ===")
    
    # Get current time
    now = timezone.now()
    today = now.date()
    
    # Create appointment time 30 minutes ago (well past 15-minute grace period)
    past_time = (now - timedelta(minutes=30)).time()
    
    print(f"Current time: {now}")
    print(f"Creating appointment for: {past_time} (30 minutes ago)")
    
    # Get first available patient, doctor, clinic
    try:
        patient = Patient.objects.first()
        doctor = Doctor.objects.first()
        clinic = Clinic.objects.first()
        
        if not all([patient, doctor, clinic]):
            print("ERROR: Need at least one Patient, Doctor, and Clinic in database")
            return
        
        # Create test token
        token = Token.objects.create(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            date=today,
            appointment_time=past_time,
            status='waiting',
            token_number=f'TEST-{now.strftime("%H%M%S")}'
        )
        
        print(f"✅ Created test token {token.id}:")
        print(f"   Patient: {patient.name}")
        print(f"   Doctor: {doctor.name}")
        print(f"   Time: {past_time}")
        print(f"   Status: {token.status}")
        
        return token
        
    except Exception as e:
        print(f"ERROR creating token: {e}")
        return None

def test_cancellation_now():
    print("\n=== Testing Cancellation Logic ===")
    
    # Run the cancellation task
    result = check_and_cancel_missed_slots()
    print(f"Cancellation result: {result}")
    
    # Check what happened to our test token
    test_tokens = Token.objects.filter(
        token_number__startswith='TEST-',
        date=timezone.now().date()
    )
    
    print(f"\nTest tokens after cancellation:")
    for token in test_tokens:
        print(f"  Token {token.id}: {token.patient.name} - Status: {token.status} - Time: {token.appointment_time}")

if __name__ == '__main__':
    # Create test token
    token = create_test_token()
    
    if token:
        # Test cancellation
        test_cancellation_now()
    else:
        print("Could not create test token")