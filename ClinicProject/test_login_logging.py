#!/usr/bin/env python
"""
Test login logging functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from api.models import Patient, Doctor, Receptionist, Clinic

def test_login_logging():
    """Test that login attempts are properly logged"""
    print("=== Testing Login Logging ===")
    
    client = Client()
    
    # Test 1: Invalid login (should log warning)
    print("\n1. Testing invalid login...")
    response = client.post('/api/login/', {
        'username': 'nonexistent_user',
        'password': 'wrong_password'
    })
    print(f"   Status: {response.status_code}")
    print("   Check Django terminal for: 'Login attempt for username: nonexistent_user'")
    print("   Check Django terminal for: 'Login failed - invalid credentials'")
    
    # Test 2: Staff login endpoint
    print("\n2. Testing staff login endpoint...")
    response = client.post('/api/login/staff/', {
        'username': 'test_staff',
        'password': 'wrong_password'
    })
    print(f"   Status: {response.status_code}")
    print("   Check Django terminal for: 'Staff login attempt for username: test_staff'")
    print("   Check Django terminal for: 'Staff login failed - invalid credentials'")
    
    # Test 3: IVR endpoint logging
    print("\n3. Testing IVR logging...")
    response = client.post('/api/ivr/welcome/', {
        'From': '+1234567890',
        'CallSid': 'test_call_456'
    })
    print(f"   Status: {response.status_code}")
    print("   Check Django terminal for: 'IVR Welcome called - Method: POST, From: +1234567890'")
    
    print("\n=== Login Logging Test Complete ===")
    print("\nWhat to look for in Django terminal:")
    print("- [timestamp] INFO api.views: Login attempt for username: ...")
    print("- [timestamp] WARNING api.views: Login failed - invalid credentials for username: ...")
    print("- [timestamp] INFO api.views: Staff login attempt for username: ...")
    print("- [timestamp] INFO api.ivr: IVR Welcome called - Method: POST, From: ...")
    print("\nIf you see these messages, logging is working correctly!")

if __name__ == '__main__':
    test_login_logging()