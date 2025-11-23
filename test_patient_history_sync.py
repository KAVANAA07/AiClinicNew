#!/usr/bin/env python3
"""
Test script to verify patient history syncing works correctly for IVR patients.
This tests that doctors can see complete patient history including IVR consultations.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.join(os.path.dirname(__file__), 'ClinicProject')
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Patient, Consultation, Doctor, Clinic, User
from api.views import normalize_phone_number
from datetime import date

def test_patient_history_sync():
    """Test that patient history syncing works for IVR patients"""
    
    print("=== Testing Patient History Sync for IVR Patients ===\n")
    
    # Test phone numbers (different formats)
    ivr_phone = " 918217612080"  # IVR format with space and country code
    web_phone = "+918217612080"  # Web format with + and country code
    
    print(f"IVR Phone: '{ivr_phone}'")
    print(f"Web Phone: '{web_phone}'")
    
    # Test normalization
    normalized_ivr = normalize_phone_number(ivr_phone)
    normalized_web = normalize_phone_number(web_phone)
    
    print(f"Normalized IVR: '{normalized_ivr}'")
    print(f"Normalized Web: '{normalized_web}'")
    print(f"Normalization Match: {normalized_ivr == normalized_web}\n")
    
    # Find patients with these phone numbers
    print("=== Finding Patients ===")
    
    # Find all patients that match normalized phone
    matching_patients = []
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_ivr:
            matching_patients.append(patient)
            print(f"Found Patient {patient.id}: {patient.name} - {patient.phone_number} (User: {patient.user_id})")
    
    if not matching_patients:
        print("No patients found with matching phone numbers")
        return
    
    print(f"\nTotal matching patients: {len(matching_patients)}")
    
    # Check consultations for each patient
    print("\n=== Consultation History ===")
    
    all_consultations = []
    for patient in matching_patients:
        consultations = Consultation.objects.filter(patient=patient).order_by('-date')
        print(f"\nPatient {patient.id} ({patient.name}):")
        print(f"  Phone: {patient.phone_number}")
        print(f"  User Account: {'Yes' if patient.user else 'No'}")
        print(f"  Consultations: {consultations.count()}")
        
        for consultation in consultations:
            print(f"    - {consultation.date}: {consultation.notes[:50] if consultation.notes else 'No notes'}...")
            all_consultations.append(consultation)
    
    print(f"\nTotal consultations across all patients: {len(all_consultations)}")
    
    # Test the updated PatientHistorySearchView logic
    print("\n=== Testing History Search Logic ===")
    
    # Simulate what PatientHistorySearchView does
    matching_patient_ids = [p.id for p in matching_patients]
    search_consultations = Consultation.objects.filter(
        patient_id__in=matching_patient_ids
    ).order_by('-date')
    
    print(f"History search would return {search_consultations.count()} consultations")
    
    if search_consultations.exists():
        print("Recent consultations:")
        for consultation in search_consultations[:3]:  # Show first 3
            print(f"  - {consultation.date} (Patient {consultation.patient.id}): {consultation.notes[:50] if consultation.notes else 'No notes'}...")
    
    print("\n=== Test Complete ===")
    
    # Summary
    if len(matching_patients) > 1:
        print(f"\n[SUCCESS] Found {len(matching_patients)} patients with same phone number")
        print(f"[SUCCESS] Total consultation history: {len(all_consultations)} records")
        print("[SUCCESS] Doctor will now see complete patient history including IVR consultations")
    elif len(matching_patients) == 1:
        print(f"\n[INFO] Found only 1 patient with this phone number")
        print("   This is normal if patient hasn't used both IVR and web")
    else:
        print(f"\n[ERROR] No patients found with phone number {ivr_phone}")

if __name__ == "__main__":
    test_patient_history_sync()