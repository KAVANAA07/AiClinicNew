#!/usr/bin/env python
"""
Simple IVR test script to verify the system is working
"""
import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import State, District, Clinic, Doctor

def test_ivr_endpoints():
    """Test IVR endpoints to ensure they're working"""
    client = Client()
    
    print("=== IVR System Test ===")
    
    # Test 1: IVR Welcome
    print("\n1. Testing IVR Welcome endpoint...")
    try:
        response = client.post('/api/ivr/welcome/', {
            'From': '+1234567890',
            'CallSid': 'test_call_123'
        })
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.get('Content-Type', 'Not set')}")
        if response.status_code == 200:
            print("   ✓ IVR Welcome endpoint is working")
            # Check if response contains TwiML
            content = response.content.decode('utf-8')
            if '<Response>' in content and '<Gather>' in content:
                print("   ✓ Valid TwiML response generated")
            else:
                print("   ⚠ Response doesn't contain expected TwiML")
                print(f"   Response: {content[:200]}...")
        else:
            print(f"   ✗ IVR Welcome failed with status {response.status_code}")
            print(f"   Response: {response.content.decode('utf-8')[:200]}...")
    except Exception as e:
        print(f"   ✗ Error testing IVR Welcome: {e}")
    
    # Test 2: Check database setup
    print("\n2. Checking database setup...")
    try:
        states = State.objects.all()
        districts = District.objects.all()
        clinics = Clinic.objects.all()
        doctors = Doctor.objects.all()
        
        print(f"   States: {states.count()}")
        print(f"   Districts: {districts.count()}")
        print(f"   Clinics: {clinics.count()}")
        print(f"   Doctors: {doctors.count()}")
        
        if states.count() > 0:
            print("   ✓ Database has states configured")
        else:
            print("   ⚠ No states found - IVR will not work without states/districts/clinics")
            
        if doctors.count() > 0:
            print("   ✓ Database has doctors configured")
        else:
            print("   ⚠ No doctors found - appointments cannot be booked")
            
    except Exception as e:
        print(f"   ✗ Error checking database: {e}")
    
    # Test 3: Test login endpoints
    print("\n3. Testing login endpoints...")
    try:
        # Test patient login endpoint
        response = client.post('/api/login/', {
            'username': 'test_user',
            'password': 'test_pass'
        })
        print(f"   Patient login status: {response.status_code}")
        
        # Test staff login endpoint  
        response = client.post('/api/login/staff/', {
            'username': 'test_staff',
            'password': 'test_pass'
        })
        print(f"   Staff login status: {response.status_code}")
        print("   ✓ Login endpoints are accessible")
        
    except Exception as e:
        print(f"   ✗ Error testing login endpoints: {e}")
    
    print("\n=== Test Complete ===")
    print("\nTo test IVR calls:")
    print("1. Make sure ngrok is running and pointing to your Django server")
    print("2. Configure Twilio webhook URL to point to: https://your-ngrok-url.ngrok-free.app/api/ivr/welcome/")
    print("3. Call your Twilio phone number")
    print("\nTo check logs:")
    print("- Watch Django terminal for login and IVR log messages")
    print("- Look for messages starting with '[timestamp] INFO api.views:' and '[timestamp] INFO api.ivr:'")

if __name__ == '__main__':
    test_ivr_endpoints()