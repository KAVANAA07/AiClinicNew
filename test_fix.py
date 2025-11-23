#!/usr/bin/env python
"""
Quick test to verify patient history search is working
"""
import os
import sys
import django

# Setup Django
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Patient, Consultation, Doctor, Clinic
from api.views import normalize_phone_number

def test_search():
    print("Testing patient history search...")
    
    # Test phone normalization
    test_phone = "9876543210"
    normalized = normalize_phone_number(test_phone)
    print(f"Phone {test_phone} normalized to: {normalized}")
    
    # Find patients
    matching_patients = []
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized:
            matching_patients.append(patient)
    
    print(f"Found {len(matching_patients)} matching patients")
    
    if matching_patients:
        # Get consultations
        patient_ids = [p.id for p in matching_patients]
        consultations = Consultation.objects.filter(patient_id__in=patient_ids)
        print(f"Found {consultations.count()} consultations")
        
        # Show patient info
        primary_patient = matching_patients[0]
        print(f"Primary patient: {primary_patient.name} - {primary_patient.phone_number}")
        
        return True
    else:
        print("No patients found")
        return False

if __name__ == "__main__":
    success = test_search()
    if success:
        print("\nSUCCESS: Patient search is working!")
        print("API endpoint: GET /api/history-search/?phone=9876543210")
    else:
        print("\nFAILED: No test data found")