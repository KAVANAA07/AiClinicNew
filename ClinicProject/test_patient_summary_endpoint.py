#!/usr/bin/env python
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from api.models import Patient, Consultation, Doctor, Clinic

def test_patient_summary_endpoint():
    print("Testing Patient Summary Endpoint...")
    
    # Create test data if needed
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testdoctor',
            defaults={'is_staff': True}
        )
        
        # Get or create auth token
        auth_token, created = Token.objects.get_or_create(user=user)
        
        # Get a patient with consultations
        patient = Patient.objects.first()
        if not patient:
            print("No patients found in database")
            return False
            
        consultations = Consultation.objects.filter(patient=patient)
        if not consultations.exists():
            print(f"No consultations found for patient {patient.id}")
            return False
            
        print(f"Testing with patient {patient.id} who has {consultations.count()} consultations")
        
        # Test the endpoint
        url = f'http://127.0.0.1:8000/api/patient-summary/{patient.id}/'
        headers = {'Authorization': f'Token {auth_token.key}'}
        
        print(f"Making request to: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Summary keys: {list(data.keys())}")
            if 'summary_text' in data:
                print(f"Summary: {data['summary_text'][:200]}...")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_patient_summary_endpoint()
    print(f"Test {'PASSED' if success else 'FAILED'}")