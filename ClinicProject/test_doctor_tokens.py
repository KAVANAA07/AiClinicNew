#!/usr/bin/env python
import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token as AuthToken
from api.models import Doctor, Token, Patient
from datetime import datetime

def test_doctor_tokens():
    print("=== Testing Doctor Token Display ===")
    
    # 1. Find a doctor user
    try:
        doctor_user = User.objects.filter(doctor__isnull=False).first()
        if not doctor_user:
            print("No doctor users found")
            return
            
        doctor = doctor_user.doctor
        print(f"Testing with doctor: {doctor.name}")
        
        # Get auth token
        token, _ = AuthToken.objects.get_or_create(user=doctor_user)
        headers = {'Authorization': f'Token {token.key}'}
        
    except Exception as e:
        print(f"Error getting doctor: {e}")
        return

    # 2. Check existing tokens for this doctor
    today = datetime.now().date()
    tokens = Token.objects.filter(doctor=doctor, date=today).exclude(status__in=['completed', 'cancelled'])
    print(f"Found {tokens.count()} active tokens for Dr. {doctor.name} today")
    
    for token in tokens:
        print(f"  - Token {token.token_number}: {token.patient.name} ({token.status})")

    # 3. Test API endpoint
    try:
        response = requests.get('http://localhost:8000/api/tokens/', headers=headers)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            api_tokens = response.json()
            print(f"API returned {len(api_tokens)} tokens")
            for token in api_tokens:
                print(f"  - API Token: {token.get('token_number')} - {token.get('patient', {}).get('name')} ({token.get('status')})")
        else:
            print(f"API Error: {response.text}")
            
    except Exception as e:
        print(f"API request error: {e}")

    # 4. Create a test token if none exist
    if tokens.count() == 0:
        print("Creating test token...")
        try:
            # Find or create a test patient
            patient, created = Patient.objects.get_or_create(
                name="Test Patient",
                defaults={'age': 30, 'phone_number': '+1234567890'}
            )
            
            # Create a test token
            test_token = Token.objects.create(
                patient=patient,
                doctor=doctor,
                clinic=doctor.clinic,
                date=today,
                status='waiting'
            )
            print(f"Created test token: {test_token.token_number}")
            
            # Test API again
            response = requests.get('http://localhost:8000/api/tokens/', headers=headers)
            if response.status_code == 200:
                api_tokens = response.json()
                print(f"After creating token, API returned {len(api_tokens)} tokens")
            
        except Exception as e:
            print(f"Error creating test token: {e}")

if __name__ == '__main__':
    test_doctor_tokens()