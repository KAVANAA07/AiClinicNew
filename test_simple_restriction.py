#!/usr/bin/env python3
"""
Simple test of the doctor restriction logic.
"""

import os
import sys
import django

# Setup Django
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Patient, Doctor, Consultation
from api.views import normalize_phone_number

User = get_user_model()

def test_restriction_logic():
    """Test the core restriction logic"""
    
    print("=== Testing Doctor Restriction Logic ===")
    
    # Get test data
    doctors = Doctor.objects.all()[:2]
    doctor1, doctor2 = doctors[0], doctors[1]
    
    test_patient = Patient.objects.filter(phone_number__isnull=False).exclude(phone_number='').first()
    
    print(f"Testing with:")
    print(f"- Dr. {doctor1.name} (ID: {doctor1.id})")
    print(f"- Dr. {doctor2.name} (ID: {doctor2.id})")
    print(f"- Patient: {test_patient.name} (Phone: {test_patient.phone_number})")
    
    # Normalize phone and find matching patients
    normalized_phone = normalize_phone_number(test_patient.phone_number)
    matching_patients = []
    
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_phone:
            matching_patients.append(patient.id)
    
    print(f"\nPhone normalization:")
    print(f"Original: {test_patient.phone_number}")
    print(f"Normalized: {normalized_phone}")
    print(f"Matching patients: {len(matching_patients)}")
    
    # Test Doctor 1 access (should work - has consultation)
    print(f"\n--- Testing Dr. {doctor1.name} Access ---")
    doctor1_consultations = Consultation.objects.filter(
        doctor=doctor1,
        patient_id__in=matching_patients
    )
    
    print(f"Consultations by Dr. {doctor1.name}: {doctor1_consultations.count()}")
    
    if doctor1_consultations.exists():
        print(f"[OK] Dr. {doctor1.name} HAS consulted this patient - ACCESS ALLOWED")
        for consultation in doctor1_consultations:
            print(f"   - {consultation.date}: {consultation.notes[:50]}...")
    else:
        print(f"[DENY] Dr. {doctor1.name} has NOT consulted this patient - ACCESS DENIED")
    
    # Test Doctor 2 access (should be blocked - no consultation)
    print(f"\n--- Testing Dr. {doctor2.name} Access ---")
    doctor2_consultations = Consultation.objects.filter(
        doctor=doctor2,
        patient_id__in=matching_patients
    )
    
    print(f"Consultations by Dr. {doctor2.name}: {doctor2_consultations.count()}")
    
    if doctor2_consultations.exists():
        print(f"[WARN] Dr. {doctor2.name} HAS consulted this patient - ACCESS ALLOWED")
        for consultation in doctor2_consultations:
            print(f"   - {consultation.date}: {consultation.notes[:50]}...")
    else:
        print(f"[OK] Dr. {doctor2.name} has NOT consulted this patient - ACCESS DENIED")
    
    # Test the actual API logic simulation
    print(f"\n--- Simulating API Logic ---")
    
    def simulate_api_check(doctor, phone):
        """Simulate the API restriction check"""
        normalized_phone = normalize_phone_number(phone)
        matching_patients = []
        
        for patient in Patient.objects.all():
            if normalize_phone_number(patient.phone_number) == normalized_phone:
                matching_patients.append(patient.id)
        
        if not matching_patients:
            return False, "Patient not found"
        
        # Check if doctor has consulted these patients
        doctor_consultations = Consultation.objects.filter(
            doctor=doctor,
            patient_id__in=matching_patients
        )
        
        if not doctor_consultations.exists():
            return False, "Access denied. You can only search history of patients you have previously consulted."
        
        return True, f"Access granted. Found {doctor_consultations.count()} consultations."
    
    # Test both doctors
    allowed1, msg1 = simulate_api_check(doctor1, test_patient.phone_number)
    allowed2, msg2 = simulate_api_check(doctor2, test_patient.phone_number)
    
    print(f"Dr. {doctor1.name}: {'[ALLOWED]' if allowed1 else '[DENIED]'} - {msg1}")
    print(f"Dr. {doctor2.name}: {'[ALLOWED]' if allowed2 else '[DENIED]'} - {msg2}")
    
    # Summary
    print(f"\n=== Test Summary ===")
    if allowed1 and not allowed2:
        print("[SUCCESS] Restriction logic working correctly!")
        print("- Doctor with previous consultation can access history")
        print("- Doctor without previous consultation is blocked")
    else:
        print("[ERROR] Restriction logic has issues")
        print(f"- Dr. {doctor1.name} (should be allowed): {'PASS' if allowed1 else 'FAIL'}")
        print(f"- Dr. {doctor2.name} (should be blocked): {'PASS' if not allowed2 else 'FAIL'}")

if __name__ == "__main__":
    test_restriction_logic()