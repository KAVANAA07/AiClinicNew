#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import Client

def test_ivr_endpoints():
    """Test all IVR endpoints"""
    client = Client()
    
    print("=== Testing IVR Endpoints ===")
    
    # Test 1: IVR Welcome
    print("\n1. Testing IVR Welcome...")
    response = client.post('/api/ivr/welcome/', {
        'From': '+1234567890',
        'CallSid': 'test_call_123'
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Welcome to ClinicFlow' in content:
            print("   [OK] IVR Welcome working")
        else:
            print("   [ERROR] Unexpected response")
            print(f"   Content: {content[:200]}...")
    else:
        print(f"   [ERROR] Failed with status {response.status_code}")
    
    # Test 2: Handle State
    print("\n2. Testing Handle State...")
    response = client.post('/api/ivr/handle-state/', {
        'From': '+1234567890',
        'Digits': '1'
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [OK] Handle State working")
    else:
        print(f"   [ERROR] Failed with status {response.status_code}")
    
    print("\n=== IVR Test Complete ===")
    print("If all tests show [OK], IVR system is working properly.")

if __name__ == '__main__':
    test_ivr_endpoints()