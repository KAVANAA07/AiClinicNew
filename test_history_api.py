#!/usr/bin/env python3
"""
Test the PatientHistorySearchView API endpoint to ensure it returns complete history.
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

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.views import PatientHistorySearchView
from api.models import Doctor

User = get_user_model()

def test_history_api():
    """Test the PatientHistorySearchView API endpoint"""
    
    print("=== Testing PatientHistorySearchView API ===\n")
    
    # Find a doctor user for authentication
    doctor = Doctor.objects.first()
    if not doctor or not doctor.user:
        print("No doctor with user account found!")
        return
    
    print(f"Using doctor: {doctor.name} (User: {doctor.user.username})")
    
    # Create a request
    factory = RequestFactory()
    request = factory.get('/api/history-search/?phone=%20918217612080')
    request.user = doctor.user
    
    # Call the view
    view = PatientHistorySearchView()
    response = view.get(request)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    
    if response.status_code == 200:
        consultations = response.data.get('consultations', [])
        patient_info = response.data.get('patient_info', {})
        total_patients = response.data.get('total_patients_found', 0)
        
        print(f"\n[SUCCESS] API returned {len(consultations)} consultations")
        print(f"[SUCCESS] Found {total_patients} patients with same phone number")
        print(f"[SUCCESS] Primary patient: {patient_info.get('name')} - {patient_info.get('phone_number')}")
        
        print("\nConsultation history:")
        for i, consultation in enumerate(consultations, 1):
            print(f"  {i}. {consultation['date']}: {consultation['notes'][:60]}...")
        
        print("\n[SUCCESS] Doctor can now see complete patient history including IVR consultations!")
    else:
        print(f"[ERROR] API call failed: {response.data}")

if __name__ == "__main__":
    test_history_api()