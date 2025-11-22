#!/usr/bin/env python
import os
import sys
import django
import requests

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token as AuthToken
from api.models import Token, Doctor, Patient, Clinic
from django.utils import timezone

def test_doctor_login_and_tokens():
    print("=== TESTING DOCTOR LOGIN AND TOKEN RETRIEVAL ===")
    
    # Test login for each doctor
    doctors = Doctor.objects.all()
    
    for doctor in doctors:
        if not doctor.user:
            print(f"Doctor {doctor.name} has no user account - skipping")
            continue
            
        print(f"\n--- Testing Doctor: {doctor.name} (User: {doctor.user.username}) ---")
        
        # Try to login
        login_data = {
            'username': doctor.user.username,
            'password': 'password123'  # Assuming default password
        }
        
        try:
            # Test staff login
            response = requests.post('http://localhost:8000/api/login/staff/', json=login_data)
            print(f"Staff login status: {response.status_code}")
            
            if response.status_code == 200:
                login_result = response.json()
                token = login_result.get('token')
                print(f"Login successful! Token: {token[:20]}...")
                
                # Test token endpoint
                headers = {'Authorization': f'Token {token}'}
                tokens_response = requests.get('http://localhost:8000/api/tokens/', headers=headers)
                print(f"Tokens API status: {tokens_response.status_code}")
                
                if tokens_response.status_code == 200:
                    tokens_data = tokens_response.json()
                    print(f"Tokens returned: {len(tokens_data)}")
                    for token_data in tokens_data:
                        print(f"  - Token ID: {token_data.get('id')}, Patient: {token_data.get('patient', {}).get('name')}, Status: {token_data.get('status')}")
                else:
                    print(f"Tokens API error: {tokens_response.text}")
            else:
                print(f"Login failed: {response.text}")
                
        except Exception as e:
            print(f"Error testing doctor {doctor.name}: {e}")

def create_test_token_for_doctor():
    print("\n=== CREATING TEST TOKEN ===")
    
    # Get a doctor
    doctor = Doctor.objects.filter(user__isnull=False).first()
    if not doctor:
        print("No doctor with user account found")
        return
        
    # Get or create a test patient
    patient, created = Patient.objects.get_or_create(
        name="Test Patient for Doctor",
        defaults={'age': 30, 'phone_number': '+1234567890'}
    )
    
    # Create a test token
    today = timezone.now().date()
    test_token = Token.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=doctor.clinic,
        date=today,
        status='confirmed',
        appointment_time=timezone.now().time()
    )
    
    print(f"Created test token ID: {test_token.id} for doctor {doctor.name}")

if __name__ == "__main__":
    create_test_token_for_doctor()
    test_doctor_login_and_tokens()