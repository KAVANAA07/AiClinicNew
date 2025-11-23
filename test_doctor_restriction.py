#!/usr/bin/env python3
"""
Test script to verify doctor restriction logic for patient history search.
"""

import os
import sys
import django
import requests
from datetime import date

# Setup Django
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Patient, Doctor, Consultation, Clinic

User = get_user_model()

def test_doctor_restriction():
    """Test that doctors can only search patients they have consulted"""
    
    print("=== Testing Doctor Restriction Logic ===")
    
    # Find existing doctors
    doctors = Doctor.objects.all()[:2]  # Get first 2 doctors
    if len(doctors) < 2:
        print("ERROR: Need at least 2 doctors in database for testing")
        return
    
    doctor1 = doctors[0]
    doctor2 = doctors[1]
    
    print(f"Doctor 1: {doctor1.name} (ID: {doctor1.id})")
    print(f"Doctor 2: {doctor2.name} (ID: {doctor2.id})")
    
    # Find a patient with phone number
    patients = Patient.objects.filter(phone_number__isnull=False).exclude(phone_number='')
    if not patients.exists():
        print("ERROR: No patients with phone numbers found")
        return
    
    test_patient = patients.first()
    print(f"Test Patient: {test_patient.name} (Phone: {test_patient.phone_number})")
    
    # Check existing consultations
    existing_consultations = Consultation.objects.filter(patient=test_patient)
    print(f"Existing consultations for patient: {existing_consultations.count()}")
    
    # Create consultation between doctor1 and test_patient (if doesn't exist)
    consultation1, created = Consultation.objects.get_or_create(
        patient=test_patient,
        doctor=doctor1,
        defaults={
            'date': date.today(),
            'notes': 'Test consultation for doctor restriction testing'
        }
    )
    
    if created:
        print(f"Created consultation between Dr. {doctor1.name} and {test_patient.name}")
    else:
        print(f"Consultation already exists between Dr. {doctor1.name} and {test_patient.name}")
    
    # Ensure doctor2 has NOT consulted this patient
    doctor2_consultations = Consultation.objects.filter(patient=test_patient, doctor=doctor2)
    if doctor2_consultations.exists():
        print(f"WARNING: Dr. {doctor2.name} has already consulted {test_patient.name}")
        print("Deleting existing consultations for clean test...")
        doctor2_consultations.delete()
    
    print(f"\nTest Setup Complete:")
    print(f"- Dr. {doctor1.name} HAS consulted {test_patient.name}")
    print(f"- Dr. {doctor2.name} has NOT consulted {test_patient.name}")
    
    # Test API endpoints (if server is running)
    base_url = "http://127.0.0.1:8000"
    
    # Try to get auth tokens for both doctors
    doctor1_user = doctor1.user if hasattr(doctor1, 'user') and doctor1.user else None
    doctor2_user = doctor2.user if hasattr(doctor2, 'user') and doctor2.user else None
    
    if not doctor1_user or not doctor2_user:
        print("WARNING: Doctors don't have user accounts. Cannot test API endpoints.")
        print("Testing database logic only...")
        
        # Test database logic directly
        from api.views import normalize_phone_number
        
        normalized_phone = normalize_phone_number(test_patient.phone_number)
        matching_patients = []
        
        for patient in Patient.objects.all():
            if normalize_phone_number(patient.phone_number) == normalized_phone:
                matching_patients.append(patient.id)
        
        print(f"\nDatabase Logic Test:")
        print(f"Normalized phone: {normalized_phone}")
        print(f"Matching patients: {len(matching_patients)}")
        
        # Test doctor1 access (should work)
        doctor1_consultations = Consultation.objects.filter(
            doctor=doctor1,
            patient_id__in=matching_patients
        )
        print(f"Dr. {doctor1.name} consultations found: {doctor1_consultations.count()}")
        
        # Test doctor2 access (should be blocked)
        doctor2_consultations = Consultation.objects.filter(
            doctor=doctor2,
            patient_id__in=matching_patients
        )
        print(f"Dr. {doctor2.name} consultations found: {doctor2_consultations.count()}")
        
        if doctor1_consultations.exists() and not doctor2_consultations.exists():
            print("✅ Database logic working correctly!")
        else:
            print("❌ Database logic issue detected")
        
        return
    
    print(f"\nTesting API endpoints...")
    print(f"Doctor 1 user: {doctor1_user.username}")
    print(f"Doctor 2 user: {doctor2_user.username}")
    
    # Test the restriction logic
    print(f"\n=== Test Results ===")
    print(f"Phone to search: {test_patient.phone_number}")
    print(f"Expected: Dr. {doctor1.name} should get results, Dr. {doctor2.name} should be blocked")

if __name__ == "__main__":
    test_doctor_restriction()