#!/usr/bin/env python3
"""
Debug why Doctor X is getting access.
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

def debug_doctor_access():
    """Debug doctor access issue"""
    
    print("=== Debug Doctor Access ===")
    
    test_phone = '+19991112233'
    doctor2 = Doctor.objects.get(id=2)  # Doctor X
    
    print(f"Testing Dr. {doctor2.name} (ID: {doctor2.id})")
    print(f"Phone: {test_phone}")
    
    # Step by step debug
    normalized_phone = normalize_phone_number(test_phone)
    print(f"Normalized phone: {normalized_phone}")
    
    matching_patients = []
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_phone:
            matching_patients.append(patient.id)
            print(f"  Matching patient: {patient.name} (ID: {patient.id})")
    
    print(f"Matching patient IDs: {matching_patients}")
    
    # Check consultations
    doctor_consultations = Consultation.objects.filter(
        doctor=doctor2,
        patient_id__in=matching_patients
    )
    
    print(f"Dr. {doctor2.name} consultations with these patients: {doctor_consultations.count()}")
    
    if doctor_consultations.exists():
        print("Found consultations:")
        for consultation in doctor_consultations:
            print(f"  - ID: {consultation.id}, Date: {consultation.date}")
            print(f"    Patient: {consultation.patient.name} (ID: {consultation.patient.id})")
            print(f"    Notes: {consultation.notes[:50]}...")
    else:
        print("No consultations found - should be blocked")
    
    # Check all consultations by this doctor
    all_doctor_consultations = Consultation.objects.filter(doctor=doctor2)
    print(f"\nAll consultations by Dr. {doctor2.name}: {all_doctor_consultations.count()}")
    
    for consultation in all_doctor_consultations:
        print(f"  - Patient: {consultation.patient.name} (ID: {consultation.patient.id})")
        print(f"    Phone: {consultation.patient.phone_number}")
        print(f"    Normalized: {normalize_phone_number(consultation.patient.phone_number)}")
        print(f"    Matches test phone: {normalize_phone_number(consultation.patient.phone_number) == normalized_phone}")

if __name__ == "__main__":
    debug_doctor_access()