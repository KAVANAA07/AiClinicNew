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
from api.models import Receptionist

def test_schedule_api():
    print("Testing Schedule API...")
    
    # Get the receptionist user
    try:
        receptionist_user = User.objects.get(username='rece')
        print(f"Found receptionist user: {receptionist_user.username}")
        
        # Get or create auth token
        token, created = Token.objects.get_or_create(user=receptionist_user)
        print(f"Auth token: {token.key}")
        
        # Test the API endpoint
        headers = {'Authorization': f'Token {token.key}'}
        response = requests.get('http://localhost:8000/api/schedules/', headers=headers)
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} schedules")
            for schedule in data:
                print(f"  Doctor: {schedule.get('doctor_name')} - {schedule.get('start_time')} to {schedule.get('end_time')}")
        
    except User.DoesNotExist:
        print("Receptionist user 'rece' not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_schedule_api()