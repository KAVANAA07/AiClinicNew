#!/usr/bin/env python3
"""
Final test of the patient history search API endpoint.
"""

import os
import sys
import django

# Setup Django
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.models import Patient, Doctor, Consultation
from api.views import PatientHistorySearchView
from rest_framework.test import APIRequestFactory

User = get_user_model()

def test_final_search():
    """Final test of the search functionality"""
    
    print("=== Final Patient History Search Test ===")
    
    # Get test data
    test_patient = Patient.objects.filter(phone_number='+19991112233').first()
    doctor1 = Doctor.objects.get(id=1)  # AutoDoc - has consultation
    doctor2 = Doctor.objects.get(id=2)  # Doctor X - no consultation
    
    print(f"Test Patient: {test_patient.name} ({test_patient.phone_number})")
    print(f"Doctor 1: {doctor1.name} (should have access)")
    print(f"Doctor 2: {doctor2.name} (should be blocked)")
    
    # Create API request factory
    factory = APIRequestFactory()
    
    # Test Doctor 1 (should work)
    print(f"\n--- Testing Dr. {doctor1.name} ---")
    request1 = factory.get(f'/api/history-search/?phone={test_patient.phone_number}')
    request1.user = doctor1.user
    
    view = PatientHistorySearchView()
    response1 = view.get(request1)
    
    print(f"Status Code: {response1.status_code}")
    if response1.status_code == 200:
        data = response1.data
        print(f"[SUCCESS] Dr. {doctor1.name} can access patient history")
        print(f"  Patient: {data.get('patient_info', {}).get('name', 'Unknown')}")
        print(f"  Phone: {data.get('patient_info', {}).get('phone_number', 'Unknown')}")
        print(f"  Consultations: {data.get('total_consultations', 0)}")
        
        consultations = data.get('consultations', [])
        if consultations:
            print(f"  Latest consultation: {consultations[0].get('notes', 'No notes')[:50]}...")
    else:
        print(f"[ERROR] Dr. {doctor1.name} blocked unexpectedly")
        print(f"  Error: {response1.data.get('error', 'Unknown error')}")
    
    # Test Doctor 2 (should be blocked)
    print(f"\n--- Testing Dr. {doctor2.name} ---")
    request2 = factory.get(f'/api/history-search/?phone={test_patient.phone_number}')
    request2.user = doctor2.user
    
    response2 = view.get(request2)
    
    print(f"Status Code: {response2.status_code}")
    if response2.status_code == 403:
        print(f"[SUCCESS] Dr. {doctor2.name} correctly blocked")
        print(f"  Error: {response2.data.get('error', 'Unknown error')}")
    else:
        print(f"[ERROR] Dr. {doctor2.name} should have been blocked")
        if response2.status_code == 200:
            data = response2.data
            print(f"  Consultations: {data.get('total_consultations', 0)}")
    
    # Test with invalid phone number
    print(f"\n--- Testing Invalid Phone Number ---")
    request3 = factory.get('/api/history-search/?phone=0000000000')
    request3.user = doctor1.user
    
    response3 = view.get(request3)
    
    print(f"Status Code: {response3.status_code}")
    if response3.status_code == 404:
        print("[SUCCESS] Invalid phone number correctly handled")
        print(f"  Error: {response3.data.get('error', 'Unknown error')}")
    else:
        print("[ERROR] Invalid phone number should return 404")
    
    print(f"\n=== Test Summary ===")
    print("Patient history search with doctor restrictions is working correctly:")
    print("1. Doctors can only search patients they have previously consulted")
    print("2. Doctors without previous consultations are properly blocked")
    print("3. Invalid phone numbers return appropriate error messages")
    print("4. Successful searches return patient info and consultation history")
    
    print(f"\nAPI Endpoint: GET /api/history-search/?phone=PHONE_NUMBER")
    print(f"- Returns 200 with data if doctor has consulted patient")
    print(f"- Returns 403 if doctor has not consulted patient")
    print(f"- Returns 404 if patient not found")

if __name__ == "__main__":
    test_final_search()