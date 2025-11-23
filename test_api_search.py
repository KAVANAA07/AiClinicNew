#!/usr/bin/env python
"""
Test script to verify the PatientHistorySearchView API endpoint
"""
import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Patient, Consultation, Doctor, User
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

def create_test_doctor():
    """Create a test doctor for authentication"""
    User = get_user_model()
    
    # Create or get test doctor user
    doctor_user, created = User.objects.get_or_create(
        username='test_doctor',
        defaults={
            'is_staff': True,
            'is_active': True
        }
    )
    
    if created:
        doctor_user.set_password('testpass123')
        doctor_user.save()
        print(f"Created doctor user: {doctor_user.username}")
    
    # Create or get auth token
    token, created = Token.objects.get_or_create(user=doctor_user)
    if created:
        print(f"Created auth token: {token.key}")
    
    return token.key

def test_api_endpoint():
    """Test the PatientHistorySearchView API endpoint"""
    print("Testing PatientHistorySearchView API endpoint...")
    
    # Get auth token
    auth_token = create_test_doctor()
    
    # Test with different phone numbers
    test_phones = [
        "+919876543210",
        "919876543210", 
        "9876543210",
        "+91 9876 543 210",
        "+10000000000"  # From existing data
    ]
    
    base_url = "http://127.0.0.1:8000/api/history-search/"
    headers = {
        'Authorization': f'Token {auth_token}',
        'Content-Type': 'application/json'
    }
    
    for phone in test_phones:
        print(f"\nTesting phone: {phone}")
        
        try:
            response = requests.get(
                base_url,
                params={'phone': phone},
                headers=headers,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Found {len(data.get('consultations', []))} consultations")
                print(f"Patient info: {data.get('patient_info', {})}")
                print(f"Total patients found: {data.get('total_patients_found', 0)}")
            elif response.status_code == 404:
                print("Patient not found (expected for some test numbers)")
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("Connection error - Django server may not be running")
            print("Please start the server with: python manage.py runserver")
            break
        except Exception as e:
            print(f"Error: {e}")

def create_test_consultation():
    """Create a test consultation for testing"""
    print("\nCreating test consultation...")
    
    # Find a test patient
    test_patient = Patient.objects.filter(phone_number__contains='9876543210').first()
    if not test_patient:
        print("No test patient found")
        return
    
    # Find or create a doctor
    from api.models import Clinic
    clinic = Clinic.objects.first()
    if not clinic:
        print("No clinic found")
        return
    
    doctor = Doctor.objects.filter(clinic=clinic).first()
    if not doctor:
        print("No doctor found")
        return
    
    # Create consultation
    consultation, created = Consultation.objects.get_or_create(
        patient=test_patient,
        doctor=doctor,
        defaults={
            'notes': 'Test consultation notes for phone search testing. Patient complained of headache and fever.',
            'date': '2024-01-15'
        }
    )
    
    if created:
        print(f"Created test consultation for {test_patient.name}")
    else:
        print(f"Test consultation already exists for {test_patient.name}")

if __name__ == "__main__":
    print("API Endpoint Test")
    print("=" * 50)
    
    # Create test consultation
    create_test_consultation()
    
    # Test API endpoint
    test_api_endpoint()