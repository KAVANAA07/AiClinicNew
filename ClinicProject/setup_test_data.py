#!/usr/bin/env python
"""
Setup basic test data for IVR system
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import State, District, Clinic, Doctor
from django.contrib.auth.models import User

def setup_basic_data():
    """Setup minimal data needed for IVR to work"""
    print("=== Setting up basic test data ===")
    
    # Create a state if none exists
    state, created = State.objects.get_or_create(name="Test State")
    if created:
        print(f"✓ Created state: {state.name}")
    else:
        print(f"✓ State exists: {state.name}")
    
    # Create a district
    district, created = District.objects.get_or_create(
        name="Test District",
        state=state
    )
    if created:
        print(f"✓ Created district: {district.name}")
    else:
        print(f"✓ District exists: {district.name}")
    
    # Create a clinic
    clinic, created = Clinic.objects.get_or_create(
        name="Test Clinic",
        defaults={
            'address': "123 Test Street",
            'city': "Test City",
            'district': district,
            'latitude': 40.7128,
            'longitude': -74.0060
        }
    )
    if created:
        print(f"✓ Created clinic: {clinic.name}")
    else:
        print(f"✓ Clinic exists: {clinic.name}")
    
    # Create a doctor
    doctor, created = Doctor.objects.get_or_create(
        name="Dr. Test",
        defaults={
            'specialization': "General Medicine",
            'clinic': clinic
        }
    )
    if created:
        print(f"✓ Created doctor: {doctor.name}")
    else:
        print(f"✓ Doctor exists: {doctor.name}")
    
    print("\n=== Test data setup complete ===")
    print(f"States: {State.objects.count()}")
    print(f"Districts: {District.objects.count()}")
    print(f"Clinics: {Clinic.objects.count()}")
    print(f"Doctors: {Doctor.objects.count()}")
    
    print("\nIVR system should now be functional!")
    print("Test by calling: python test_ivr.py")

if __name__ == '__main__':
    setup_basic_data()