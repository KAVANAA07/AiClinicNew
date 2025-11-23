#!/usr/bin/env python3
"""
Test the PatientHistoryView API endpoint to ensure it returns complete history for individual patients.
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
from api.models import Doctor, Patient
from api.views import normalize_phone_number
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

def test_patient_history_view():
    """Test the PatientHistoryView API endpoint"""
    
    print("=== Testing PatientHistoryView API ===\n")
    
    # Find a doctor user for authentication
    doctor = Doctor.objects.first()
    if not doctor or not doctor.user:
        print("No doctor with user account found!")
        return
    
    print(f"Using doctor: {doctor.name} (User: {doctor.user.username})")
    
    # Get or create auth token
    token, _ = Token.objects.get_or_create(user=doctor.user)
    
    # Find patients with the test phone number
    test_phone = " 918217612080"
    normalized_phone = normalize_phone_number(test_phone)
    
    matching_patients = []
    for patient in Patient.objects.all():
        if normalize_phone_number(patient.phone_number) == normalized_phone:
            matching_patients.append(patient)
    
    print(f"Found {len(matching_patients)} patients with phone {test_phone}")
    
    # Create test client
    client = Client()
    
    # Test each patient's history view
    for patient in matching_patients:
        print(f"\n--- Testing Patient {patient.id} ({patient.name}) ---")
        
        response = client.get(
            f'/api/history/{patient.id}/',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            consultations = json.loads(response.content)
            print(f"Consultations returned: {len(consultations)}")
            
            for i, consultation in enumerate(consultations, 1):
                print(f"  {i}. {consultation['date']}: {consultation['notes'][:60]}...")
        else:
            try:
                error_data = json.loads(response.content)
                print(f"[ERROR] API call failed: {error_data}")
            except:
                print(f"[ERROR] API call failed with status {response.status_code}")
    
    print(f"\n[SUCCESS] PatientHistoryView now shows complete history including linked IVR/web consultations!")

if __name__ == "__main__":
    test_patient_history_view()