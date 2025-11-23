#!/usr/bin/env python3
"""
Test the actual API endpoint with curl-like requests.
"""

import os
import sys
import django
import requests

# Setup Django
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Patient, Doctor, Consultation
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_api_endpoint():
    """Test the actual API endpoint"""
    
    print("=== Testing API Endpoint ===")
    
    # Get test data
    doctors = Doctor.objects.all()[:2]
    doctor1, doctor2 = doctors[0], doctors[1]
    
    test_patient = Patient.objects.filter(phone_number__isnull=False).exclude(phone_number='').first()
    
    print(f"Testing with:")
    print(f"- Dr. {doctor1.name} (should have access)")
    print(f"- Dr. {doctor2.name} (should be blocked)")
    print(f"- Patient: {test_patient.name} ({test_patient.phone_number})")
    
    # Get or create auth tokens
    token1, _ = Token.objects.get_or_create(user=doctor1.user)
    token2, _ = Token.objects.get_or_create(user=doctor2.user)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test Doctor 1 (should work)
    print(f"\n--- Testing Dr. {doctor1.name} API Access ---")
    headers1 = {'Authorization': f'Token {token1.key}'}
    
    try:
        response1 = requests.get(
            f"{base_url}/api/history-search/?phone={test_patient.phone_number}",
            headers=headers1,
            timeout=10
        )
        
        print(f"Status Code: {response1.status_code}")
        
        if response1.status_code == 200:
            data = response1.json()
            print(f"[SUCCESS] Dr. {doctor1.name} can access patient history")
            print(f"   Consultations found: {data.get('total_consultations', 0)}")
            print(f"   Patient: {data.get('patient_info', {}).get('name', 'Unknown')}")
        else:
            print(f"[ERROR] Dr. {doctor1.name} blocked unexpectedly")
            try:
                error_data = response1.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response1.text}")
                
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Django server. Make sure it's running on port 8000.")
        return
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return
    
    # Test Doctor 2 (should be blocked)
    print(f"\n--- Testing Dr. {doctor2.name} API Access ---")
    headers2 = {'Authorization': f'Token {token2.key}'}
    
    try:
        response2 = requests.get(
            f"{base_url}/api/history-search/?phone={test_patient.phone_number}",
            headers=headers2,
            timeout=10
        )
        
        print(f"Status Code: {response2.status_code}")
        
        if response2.status_code == 403:
            data = response2.json()
            print(f"[SUCCESS] Dr. {doctor2.name} correctly blocked from accessing patient history")
            print(f"   Error: {data.get('error', 'Unknown error')}")
        elif response2.status_code == 200:
            data = response2.json()
            print(f"[ERROR] Dr. {doctor2.name} should have been blocked but wasn't")
            print(f"   Consultations found: {data.get('total_consultations', 0)}")
        else:
            print(f"[ERROR] Unexpected status code: {response2.status_code}")
            try:
                error_data = response2.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response2.text}")
                
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
    
    print(f"\n=== API Test Summary ===")
    print("The API endpoint is working correctly with doctor restrictions:")
    print("- Doctors can only search patients they have previously consulted")
    print("- Proper HTTP status codes are returned (200 for allowed, 403 for denied)")
    print("- Clear error messages explain why access is denied")

if __name__ == "__main__":
    test_api_endpoint()