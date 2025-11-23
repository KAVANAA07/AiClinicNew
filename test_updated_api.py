#!/usr/bin/env python3
"""
Test the updated API response.
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
from api.views import PatientHistorySearchView
from rest_framework.test import APIRequestFactory
import json

User = get_user_model()

def test_updated_api():
    """Test the updated API"""
    
    print("=== Testing Updated API ===")
    
    # Get test data
    doctor1 = Doctor.objects.get(id=1)  # AutoDoc
    test_phone = '+19991112233'
    
    print(f"Testing with Dr. {doctor1.name} and phone {test_phone}")
    
    # Create a mock request object
    class MockRequest:
        def __init__(self, user, phone):
            self.user = user
            self.query_params = {'phone': phone}
    
    # Create the view and mock request
    view = PatientHistorySearchView()
    mock_request = MockRequest(doctor1.user, test_phone)
    
    # Call the view method directly
    response = view.get(mock_request)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Data:")
    
    # Pretty print the response data
    response_json = json.dumps(response.data, indent=2, default=str)
    print(response_json)
    
    # Check key fields
    if response.status_code == 200:
        data = response.data
        print(f"\n=== Key Information ===")
        print(f"Success: {data.get('success', False)}")
        print(f"Message: {data.get('message', 'No message')}")
        print(f"Total Consultations: {data.get('total_consultations', 0)}")
        print(f"Patient Name: {data.get('patient_info', {}).get('name', 'Unknown')}")
        
        consultations = data.get('consultations', [])
        print(f"Consultations Array Length: {len(consultations)}")
        
        if consultations:
            print(f"First Consultation:")
            first = consultations[0]
            print(f"  ID: {first.get('id', 'N/A')}")
            print(f"  Date: {first.get('date', 'N/A')}")
            print(f"  Notes: {first.get('notes', 'N/A')[:50]}...")
        else:
            print("No consultations in response!")
    
    # Test the POST method (test endpoint)
    print(f"\n=== Testing POST Method (Test Endpoint) ===")
    post_response = view.post(mock_request)
    print(f"POST Status: {post_response.status_code}")
    
    if post_response.status_code == 200:
        post_data = post_response.data
        print(f"POST Success: {post_data.get('success', False)}")
        print(f"POST Message: {post_data.get('message', 'No message')}")
        print(f"Test Consultations: {len(post_data.get('test_consultations', []))}")

if __name__ == "__main__":
    test_updated_api()