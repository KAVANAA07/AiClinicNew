#!/usr/bin/env python3
"""
Debug script to check what's happening with patient history search.
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

def debug_search():
    """Debug the patient history search"""
    
    print("=== Debugging Patient History Search ===")
    
    # Get test data
    doctors = Doctor.objects.all()[:2]
    if len(doctors) < 2:
        print("ERROR: Need at least 2 doctors")
        return
    
    doctor1, doctor2 = doctors[0], doctors[1]
    
    # Find a patient with consultations
    patients_with_consultations = []
    for patient in Patient.objects.filter(phone_number__isnull=False).exclude(phone_number=''):
        consultation_count = Consultation.objects.filter(patient=patient).count()
        if consultation_count > 0:
            patients_with_consultations.append((patient, consultation_count))
    
    if not patients_with_consultations:
        print("ERROR: No patients with consultations found")
        return
    
    # Use patient with most consultations
    test_patient, consultation_count = max(patients_with_consultations, key=lambda x: x[1])
    
    print(f"Test Patient: {test_patient.name} (Phone: {test_patient.phone_number})")
    print(f"Total consultations: {consultation_count}")
    
    # Check phone normalization
    normalized_phone = normalize_phone_number(test_patient.phone_number)
    print(f"Normalized phone: {normalized_phone}")
    
    # Find matching patients
    matching_patients = []
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_phone:
            matching_patients.append(patient.id)
    
    print(f"Matching patients: {len(matching_patients)} - IDs: {matching_patients}")
    
    # Check consultations for each doctor
    print(f"\n--- Doctor Consultation Analysis ---")
    
    for doctor in [doctor1, doctor2]:
        doctor_consultations = Consultation.objects.filter(
            doctor=doctor,
            patient_id__in=matching_patients
        )
        
        print(f"\nDr. {doctor.name}:")
        print(f"  Consultations: {doctor_consultations.count()}")
        
        if doctor_consultations.exists():
            print("  Details:")
            for consultation in doctor_consultations:
                print(f"    - {consultation.date}: {consultation.notes[:50]}...")
        else:
            print("  No consultations found")
    
    # Check all consultations for these patients
    all_consultations = Consultation.objects.filter(
        patient_id__in=matching_patients
    ).order_by('-date')
    
    print(f"\n--- All Consultations for Matching Patients ---")
    print(f"Total consultations: {all_consultations.count()}")
    
    if all_consultations.exists():
        print("Details:")
        for consultation in all_consultations:
            print(f"  - {consultation.date} by Dr. {consultation.doctor.name}: {consultation.notes[:50]}...")
    else:
        print("No consultations found!")
    
    # Test the API logic simulation
    print(f"\n--- API Logic Simulation ---")
    
    def simulate_search(user_doctor, phone):
        """Simulate the search logic"""
        normalized_phone = normalize_phone_number(phone)
        matching_patients = []
        
        for patient in Patient.objects.all():
            if normalize_phone_number(patient.phone_number) == normalized_phone:
                matching_patients.append(patient.id)
        
        if not matching_patients:
            return False, "Patient not found", []
        
        if user_doctor:
            # Doctor restriction
            doctor_consultations = Consultation.objects.filter(
                doctor=user_doctor,
                patient_id__in=matching_patients
            )
            
            if not doctor_consultations.exists():
                return False, "Access denied", []
            
            consultations = doctor_consultations.order_by('-date')
        else:
            # Non-doctor user
            consultations = Consultation.objects.filter(
                patient_id__in=matching_patients
            ).order_by('-date')
        
        return True, f"Found {consultations.count()} consultations", list(consultations)
    
    # Test both doctors
    for doctor in [doctor1, doctor2]:
        allowed, msg, consultations = simulate_search(doctor, test_patient.phone_number)
        print(f"Dr. {doctor.name}: {'ALLOWED' if allowed else 'DENIED'} - {msg}")
        if consultations:
            print(f"  Consultations returned: {len(consultations)}")
    
    # Test non-doctor access
    allowed, msg, consultations = simulate_search(None, test_patient.phone_number)
    print(f"Non-doctor: {'ALLOWED' if allowed else 'DENIED'} - {msg}")
    if consultations:
        print(f"  Consultations returned: {len(consultations)}")

if __name__ == "__main__":
    debug_search()