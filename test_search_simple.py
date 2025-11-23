#!/usr/bin/env python
"""
Simple test for patient history search functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Patient, Consultation, Doctor, User, Clinic
from api.views import normalize_phone_number, PatientHistorySearchView
from rest_framework.test import APIRequestFactory
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

def setup_test_data():
    """Set up test data"""
    print("Setting up test data...")
    
    # Create test patients with same normalized phone
    test_phones = [
        "9876543210",
        "+919876543210", 
        "91-9876-543-210"
    ]
    
    patients = []
    for i, phone in enumerate(test_phones):
        patient, created = Patient.objects.get_or_create(
            phone_number=phone,
            defaults={
                'name': f'Test Patient {i+1}',
                'age': 25 + i
            }
        )
        patients.append(patient)
        if created:
            print(f"Created patient: {patient.name} - {patient.phone_number}")
    
    # Create test doctor and clinic
    clinic, _ = Clinic.objects.get_or_create(
        name='Test Clinic',
        defaults={'address': 'Test Address'}
    )
    
    doctor, _ = Doctor.objects.get_or_create(
        name='Test Doctor',
        defaults={
            'specialization': 'General',
            'clinic': clinic
        }
    )
    
    # Create test consultations
    for i, patient in enumerate(patients):
        consultation, created = Consultation.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            defaults={
                'notes': f'Test consultation {i+1} - Patient has fever and headache',
                'date': '2024-01-15'
            }
        )
        if created:
            print(f"Created consultation for {patient.name}")
    
    return test_phones[0]

def test_search_view():
    """Test the PatientHistorySearchView"""
    print("\nTesting PatientHistorySearchView...")
    
    # Create test user with staff permissions
    User = get_user_model()
    test_user, created = User.objects.get_or_create(
        username='test_staff',
        defaults={
            'is_staff': True,
            'is_active': True
        }
    )
    
    if created:
        test_user.set_password('testpass')
        test_user.save()
    
    # Test phone number
    test_phone = "9876543210"
    
    # Test the search logic directly
    normalized_phone = normalize_phone_number(test_phone)
    print(f"Searching for normalized phone: {normalized_phone}")
    
    # Find matching patients
    matching_patients = []
    all_patients = Patient.objects.all()
    
    for patient in all_patients:
        patient_normalized = normalize_phone_number(patient.phone_number)
        if patient_normalized == normalized_phone:
            matching_patients.append(patient.id)
            print(f"Found matching patient: {patient.name} - {patient.phone_number} -> {patient_normalized}")
    
    print(f"Total matching patients: {len(matching_patients)}")
    
    if matching_patients:
        # Get consultations
        consultations = Consultation.objects.filter(patient_id__in=matching_patients)
        print(f"Found {consultations.count()} consultations")
        
        for consultation in consultations:
            print(f"  - {consultation.patient.name}: {consultation.notes[:50]}...")
        
        return True
    else:
        print("No matching patients found")
        return False

def test_normalization():
    """Test phone number normalization"""
    print("\nTesting phone normalization...")
    
    test_cases = [
        ("9876543210", "9876543210"),
        ("+919876543210", "9876543210"),
        ("91-9876-543-210", "9876543210"),
        ("+91 9876 543 210", "9876543210")
    ]
    
    for input_phone, expected in test_cases:
        result = normalize_phone_number(input_phone)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: {input_phone} -> {result} (expected: {expected})")

if __name__ == "__main__":
    print("Patient History Search Test")
    print("=" * 50)
    
    # Test normalization
    test_normalization()
    
    # Setup test data
    test_phone = setup_test_data()
    
    # Test search view
    success = test_search_view()
    
    if success:
        print("\nSUCCESS: Patient history search is working correctly!")
        print(f"You can test with phone number: {test_phone}")
        print("\nTo test via API:")
        print(f"GET /api/history-search/?phone={test_phone}")
        print("(Make sure you're authenticated as staff/doctor)")
    else:
        print("\nFAILED: Patient history search has issues")