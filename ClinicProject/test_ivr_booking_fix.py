#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Patient, Token, Doctor, Clinic
from api.views import _create_ivr_token, normalize_phone_number
from datetime import datetime, date, time

def test_ivr_booking_restriction():
    print("Testing IVR booking restriction...")
    
    # Test phone number
    test_phone = "+1234567890"
    normalized_phone = normalize_phone_number(test_phone)
    
    # Check if there are existing patients with this phone
    matching_patients = []
    for p in Patient.objects.all():
        if normalize_phone_number(p.phone_number) == normalized_phone:
            matching_patients.append(p.id)
    
    print(f"Phone: {test_phone}")
    print(f"Normalized: {normalized_phone}")
    print(f"Matching patients: {matching_patients}")
    
    # Check for existing active tokens
    if matching_patients:
        existing_tokens = Token.objects.filter(patient_id__in=matching_patients).exclude(status__in=['completed', 'cancelled', 'skipped'])
        print(f"Existing active tokens: {existing_tokens.count()}")
        
        for token in existing_tokens:
            print(f"  Token {token.id}: Patient {token.patient.id}, Doctor {token.doctor.name}, Date {token.date}, Status {token.status}")
    
    # Test the booking function
    try:
        doctor = Doctor.objects.first()
        if doctor:
            print(f"\nTesting booking with Dr. {doctor.name}...")
            result = _create_ivr_token(doctor, date.today(), "14:00", test_phone)
            if result:
                print(f"✅ Booking successful: Token {result.id}")
            else:
                print("❌ Booking failed (as expected if patient already has active token)")
        else:
            print("No doctors found for testing")
    except Exception as e:
        print(f"Error during booking test: {e}")

if __name__ == "__main__":
    test_ivr_booking_restriction()