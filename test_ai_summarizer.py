#!/usr/bin/env python3
"""
Test the AI summarizer functionality to identify and fix issues.
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

from django.test import Client
from django.contrib.auth import get_user_model
from api.models import Doctor, Patient, Consultation
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

def test_ai_summarizer():
    """Test AI summarizer endpoints"""
    
    print("=== Testing AI Summarizer ===\n")
    
    # Find a doctor user for authentication
    doctor = Doctor.objects.first()
    if not doctor or not doctor.user:
        print("No doctor with user account found!")
        return
    
    print(f"Using doctor: {doctor.name} (User: {doctor.user.username})")
    
    # Get or create auth token
    token, _ = Token.objects.get_or_create(user=doctor.user)
    
    # Create test client
    client = Client()
    
    # Test 1: Check AI model status
    print("\n--- Testing AI Model Status ---")
    response = client.get('/api/patient-summary/status/')
    print(f"Status endpoint: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"Model loaded: {data.get('loaded')}")
        print(f"Model name: {data.get('model')}")
    
    # Test 2: Try to load AI model
    print("\n--- Testing AI Model Load ---")
    response = client.post('/api/patient-summary/load/')
    print(f"Load endpoint: {response.status_code}")
    if response.status_code in [200, 202]:
        data = json.loads(response.content)
        print(f"Load response: {data}")
    
    # Test 3: Test simple AI summary
    print("\n--- Testing Simple AI Summary ---")
    test_history = """
    Patient: John Doe
    Date: 2025-01-15
    Doctor: Dr. Smith
    Notes: Patient complained of headache and fever for 3 days. Temperature 101F. Prescribed paracetamol 500mg twice daily.
    
    Date: 2025-01-10  
    Doctor: Dr. Jones
    Notes: Routine checkup. Blood pressure normal. Patient reports feeling well.
    """
    
    response = client.post(
        '/api/ai-summary/',
        data=json.dumps({
            'patient_history': test_history,
            'phone': '1234567890'
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    
    print(f"AI Summary endpoint: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"Summary: {data.get('summary', 'No summary')[:100]}...")
        print(f"Model: {data.get('model')}")
    else:
        try:
            error_data = json.loads(response.content)
            print(f"Error: {error_data}")
        except:
            print(f"Error response: {response.content}")
    
    # Test 4: Test patient-specific summary
    print("\n--- Testing Patient-Specific Summary ---")
    
    # Find a patient with consultations
    patient_with_consultations = None
    for patient in Patient.objects.all():
        if Consultation.objects.filter(patient=patient).exists():
            patient_with_consultations = patient
            break
    
    if patient_with_consultations:
        print(f"Testing with patient: {patient_with_consultations.name} (ID: {patient_with_consultations.id})")
        
        response = client.get(
            f'/api/patient-summary/{patient_with_consultations.id}/',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        
        print(f"Patient summary endpoint: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.content)
            print(f"Summary keys: {list(data.keys())}")
            if 'summary_text' in data:
                print(f"Summary: {data['summary_text'][:100]}...")
        else:
            try:
                error_data = json.loads(response.content)
                print(f"Error: {error_data}")
            except:
                print(f"Error response: {response.content}")
    else:
        print("No patients with consultations found for testing")

if __name__ == "__main__":
    test_ai_summarizer()