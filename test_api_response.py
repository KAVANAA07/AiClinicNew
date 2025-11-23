#!/usr/bin/env python3
"""
Test what the API is actually returning.
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
from api.serializers import ConsultationSerializer

User = get_user_model()

def test_api_response():
    """Test what the API returns"""
    
    print("=== Testing API Response Format ===")
    
    # Use our test data
    test_phone = '+19991112233'
    doctor1 = Doctor.objects.get(id=1)  # AutoDoc - has consultation
    
    print(f"Testing phone: {test_phone}")
    print(f"Doctor: {doctor1.name}")
    
    # Simulate the exact API logic
    normalized_phone = normalize_phone_number(test_phone)
    matching_patients = []
    
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_phone:
            matching_patients.append(patient.id)
    
    print(f"Normalized phone: {normalized_phone}")
    print(f"Matching patients: {matching_patients}")
    
    # Get consultations (doctor restriction)
    doctor_consultations = Consultation.objects.filter(
        doctor=doctor1,
        patient_id__in=matching_patients
    )
    
    print(f"Doctor consultations found: {doctor_consultations.count()}")
    
    if doctor_consultations.exists():
        consultations = doctor_consultations.order_by('-date')
        
        # Get patient info
        primary_patient = Patient.objects.get(id=matching_patients[0])
        
        # Serialize consultations
        serializer = ConsultationSerializer(consultations, many=True)
        
        # Build response like the API
        response_data = {
            'consultations': serializer.data,
            'patient_info': {
                'name': primary_patient.name,
                'phone_number': primary_patient.phone_number,
                'age': primary_patient.age
            },
            'total_patients_found': len(matching_patients),
            'total_consultations': consultations.count()
        }
        
        print(f"\n=== API Response Data ===")
        print(f"Status: 200 OK")
        print(f"Patient Info:")
        print(f"  Name: {response_data['patient_info']['name']}")
        print(f"  Phone: {response_data['patient_info']['phone_number']}")
        print(f"  Age: {response_data['patient_info']['age']}")
        print(f"Total Patients Found: {response_data['total_patients_found']}")
        print(f"Total Consultations: {response_data['total_consultations']}")
        
        print(f"\nConsultations:")
        for i, consultation in enumerate(response_data['consultations']):
            print(f"  {i+1}. ID: {consultation.get('id', 'N/A')}")
            print(f"     Date: {consultation.get('date', 'N/A')}")
            print(f"     Doctor: {consultation.get('doctor', 'N/A')}")
            print(f"     Notes: {consultation.get('notes', 'N/A')[:50]}...")
            print()
        
        # Check if consultations array is empty
        if not response_data['consultations']:
            print("WARNING: Consultations array is empty!")
        
        # Check serializer data directly
        print(f"\n=== Raw Serializer Data ===")
        for consultation in consultations:
            print(f"Consultation ID: {consultation.id}")
            print(f"Date: {consultation.date}")
            print(f"Doctor: {consultation.doctor.name}")
            print(f"Patient: {consultation.patient.name}")
            print(f"Notes: {consultation.notes[:50]}...")
            print()
        
    else:
        print("No consultations found - doctor would be blocked")

if __name__ == "__main__":
    test_api_response()