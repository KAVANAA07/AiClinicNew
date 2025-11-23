#!/usr/bin/env python3
"""
Detailed debug script to check consultation-doctor relationships.
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

def detailed_debug():
    """Detailed debug of consultation relationships"""
    
    print("=== Detailed Consultation Debug ===")
    
    # Find patient with consultations
    test_patient = Patient.objects.filter(phone_number='+19991112233').first()
    if not test_patient:
        print("Test patient not found")
        return
    
    print(f"Test Patient: {test_patient.name} (ID: {test_patient.id}, Phone: {test_patient.phone_number})")
    
    # Get all consultations for this patient
    consultations = Consultation.objects.filter(patient=test_patient)
    print(f"Direct consultations for patient: {consultations.count()}")
    
    for consultation in consultations:
        print(f"  Consultation ID: {consultation.id}")
        print(f"  Date: {consultation.date}")
        print(f"  Doctor: {consultation.doctor.name} (ID: {consultation.doctor.id})")
        print(f"  Patient: {consultation.patient.name} (ID: {consultation.patient.id})")
        print(f"  Notes: {consultation.notes[:50]}...")
        print()
    
    # Check all doctors
    print("--- All Doctors ---")
    doctors = Doctor.objects.all()
    for doctor in doctors:
        print(f"Dr. {doctor.name} (ID: {doctor.id})")
        
        # Check consultations by this doctor
        doctor_consultations = Consultation.objects.filter(doctor=doctor)
        print(f"  Total consultations: {doctor_consultations.count()}")
        
        # Check consultations by this doctor for our test patient
        patient_consultations = Consultation.objects.filter(doctor=doctor, patient=test_patient)
        print(f"  Consultations for test patient: {patient_consultations.count()}")
        
        if patient_consultations.exists():
            for consultation in patient_consultations:
                print(f"    - {consultation.date}: {consultation.notes[:30]}...")
        print()
    
    # Check normalized phone matching
    normalized_phone = normalize_phone_number(test_patient.phone_number)
    print(f"Normalized phone: {normalized_phone}")
    
    matching_patients = []
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_phone:
            matching_patients.append(patient.id)
            print(f"  Matching patient: {patient.name} (ID: {patient.id}, Phone: {patient.phone_number})")
    
    print(f"Matching patient IDs: {matching_patients}")
    
    # Test the exact query used in the API
    print("\n--- Testing API Query Logic ---")
    
    for doctor in doctors[:2]:  # Test first 2 doctors
        print(f"\nTesting Dr. {doctor.name} (ID: {doctor.id}):")
        
        # This is the exact query from the API
        doctor_consultations = Consultation.objects.filter(
            doctor=doctor,
            patient_id__in=matching_patients
        )
        
        print(f"  Query result: {doctor_consultations.count()} consultations")
        
        if doctor_consultations.exists():
            print("  Found consultations:")
            for consultation in doctor_consultations:
                print(f"    - {consultation.date} with {consultation.patient.name}: {consultation.notes[:30]}...")
        else:
            print("  No consultations found with this query")
            
            # Debug: Check if doctor has ANY consultations
            any_consultations = Consultation.objects.filter(doctor=doctor)
            print(f"  Doctor has {any_consultations.count()} total consultations")
            
            # Debug: Check if patients have consultations with ANY doctor
            patient_consultations = Consultation.objects.filter(patient_id__in=matching_patients)
            print(f"  Patients have {patient_consultations.count()} total consultations")

if __name__ == "__main__":
    detailed_debug()