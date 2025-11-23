#!/usr/bin/env python3
"""
Create a test consultation to make the search work.
"""

import os
import sys
import django
from datetime import date

# Setup Django
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Patient, Doctor, Consultation

User = get_user_model()

def create_test_consultation():
    """Create a test consultation for testing"""
    
    print("=== Creating Test Consultation ===")
    
    # Get test patient
    test_patient = Patient.objects.filter(phone_number='+19991112233').first()
    if not test_patient:
        print("Test patient not found")
        return
    
    # Get first doctor
    doctor = Doctor.objects.first()
    if not doctor:
        print("No doctors found")
        return
    
    print(f"Creating consultation between Dr. {doctor.name} and {test_patient.name}")
    
    # Create consultation
    consultation, created = Consultation.objects.get_or_create(
        patient=test_patient,
        doctor=doctor,
        defaults={
            'date': date.today(),
            'notes': 'Test consultation for patient history search functionality. Patient complained of headache and fever. Prescribed paracetamol and advised rest.'
        }
    )
    
    if created:
        print(f"[OK] Created consultation ID: {consultation.id}")
    else:
        print(f"[EXISTS] Consultation already exists ID: {consultation.id}")
    
    print(f"Details:")
    print(f"  Patient: {consultation.patient.name} (ID: {consultation.patient.id})")
    print(f"  Doctor: {consultation.doctor.name} (ID: {consultation.doctor.id})")
    print(f"  Date: {consultation.date}")
    print(f"  Notes: {consultation.notes}")
    
    # Test the search logic now
    print(f"\n=== Testing Search Logic ===")
    
    from api.views import normalize_phone_number
    
    normalized_phone = normalize_phone_number(test_patient.phone_number)
    matching_patients = []
    
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_phone:
            matching_patients.append(patient.id)
    
    print(f"Normalized phone: {normalized_phone}")
    print(f"Matching patients: {matching_patients}")
    
    # Test doctor access
    doctor_consultations = Consultation.objects.filter(
        doctor=doctor,
        patient_id__in=matching_patients
    )
    
    print(f"Dr. {doctor.name} consultations: {doctor_consultations.count()}")
    
    if doctor_consultations.exists():
        print("[SUCCESS] Doctor can now access patient history!")
        for consultation in doctor_consultations:
            print(f"  - {consultation.date}: {consultation.notes[:50]}...")
    else:
        print("[ERROR] Still no access - something is wrong")
    
    # Test other doctors (should be blocked)
    other_doctors = Doctor.objects.exclude(id=doctor.id)[:2]
    for other_doctor in other_doctors:
        other_consultations = Consultation.objects.filter(
            doctor=other_doctor,
            patient_id__in=matching_patients
        )
        print(f"Dr. {other_doctor.name} consultations: {other_consultations.count()}")
        if other_consultations.exists():
            print(f"  [OK] Has access")
        else:
            print(f"  [BLOCKED] Blocked (correct)")

if __name__ == "__main__":
    create_test_consultation()