#!/usr/bin/env python
"""
Test script to verify phone number search functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Patient, Consultation
from api.views import normalize_phone_number

def test_phone_normalization():
    """Test phone number normalization function"""
    print("Testing phone number normalization...")
    
    test_cases = [
        ("+919876543210", "9876543210"),
        ("919876543210", "9876543210"),
        ("9876543210", "9876543210"),
        ("+1-555-123-4567", "5551234567"),
        ("15551234567", "5551234567"),
        ("555-123-4567", "5551234567"),
        ("(555) 123-4567", "5551234567"),
        ("555 123 4567", "5551234567"),
    ]
    
    for input_phone, expected in test_cases:
        result = normalize_phone_number(input_phone)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} {input_phone} -> {result} (expected: {expected})")

def test_patient_search():
    """Test patient search functionality"""
    print("\nTesting patient search...")
    
    # Get all patients
    patients = Patient.objects.all()
    print(f"Total patients in database: {patients.count()}")
    
    if patients.exists():
        # Test with first patient
        test_patient = patients.first()
        print(f"Testing with patient: {test_patient.name} - {test_patient.phone_number}")
        
        # Test normalization
        normalized = normalize_phone_number(test_patient.phone_number)
        print(f"Normalized phone: {normalized}")
        
        # Find matching patients
        matching_patients = []
        for patient in Patient.objects.all():
            if normalize_phone_number(patient.phone_number) == normalized:
                matching_patients.append(patient.id)
        
        print(f"Matching patients found: {len(matching_patients)}")
        for patient_id in matching_patients:
            patient = Patient.objects.get(id=patient_id)
            print(f"  - ID: {patient.id}, Name: {patient.name}, Phone: {patient.phone_number}")
        
        # Test consultation search
        consultations = Consultation.objects.filter(patient_id__in=matching_patients)
        print(f"Consultations found: {consultations.count()}")
        
        return test_patient.phone_number
    else:
        print("No patients found in database")
        return None

def create_test_data():
    """Create test data for phone search"""
    print("\nCreating test data...")
    
    # Create test patients with different phone formats
    test_phones = [
        "+919876543210",
        "919876543210", 
        "9876543210",
        "+91 9876 543 210"
    ]
    
    for i, phone in enumerate(test_phones):
        patient, created = Patient.objects.get_or_create(
            phone_number=phone,
            defaults={
                'name': f'Test Patient {i+1}',
                'age': 25 + i
            }
        )
        if created:
            print(f"Created patient: {patient.name} - {patient.phone_number}")
        else:
            print(f"Patient exists: {patient.name} - {patient.phone_number}")

if __name__ == "__main__":
    print("Phone Number Search Test")
    print("=" * 50)
    
    # Test normalization function
    test_phone_normalization()
    
    # Create test data
    create_test_data()
    
    # Test patient search
    test_phone = test_patient_search()
    
    if test_phone:
        print(f"\nTo test the API endpoint, use:")
        print(f"GET /api/history-search/?phone={test_phone}")