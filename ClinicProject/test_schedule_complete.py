#!/usr/bin/env python
import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from api.models import DoctorSchedule

def test_complete_schedule_flow():
    print("=== Testing Complete Schedule Management Flow ===")
    
    # 1. Get receptionist token
    try:
        user = User.objects.get(username='rece')
        token, _ = Token.objects.get_or_create(user=user)
        headers = {'Authorization': f'Token {token.key}', 'Content-Type': 'application/json'}
        print(f"Got auth token: {token.key[:10]}...")
    except Exception as e:
        print(f"Auth error: {e}")
        return

    # 2. Test GET schedules
    try:
        response = requests.get('http://localhost:8000/api/schedules/', headers=headers)
        print(f"GET /schedules/ - Status: {response.status_code}")
        if response.status_code == 200:
            schedules = response.json()
            print(f"Found {len(schedules)} schedules")
            for schedule in schedules:
                print(f"  - Doctor {schedule['doctor_name']}: {schedule['start_time']} - {schedule['end_time']}")
        else:
            print(f"GET error: {response.text}")
            return
    except Exception as e:
        print(f"GET request error: {e}")
        return

    # 3. Test PATCH schedule update
    if schedules:
        schedule = schedules[0]
        doctor_id = schedule['doctor']
        
        # Test data with different time formats
        test_updates = [
            {'start_time': '08:00', 'end_time': '18:00'},
            {'start_time': '08:00:00', 'end_time': '18:00:00'},
            {'slot_duration_minutes': 30},
            {'max_slots_per_day': 20},
            {'is_active': False}
        ]
        
        for i, update_data in enumerate(test_updates):
            try:
                print(f"\n--- Test {i+1}: Updating with {update_data} ---")
                response = requests.patch(
                    f'http://localhost:8000/api/schedules/{doctor_id}/',
                    headers=headers,
                    data=json.dumps(update_data)
                )
                print(f"PATCH Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"Update successful: {result}")
                else:
                    print(f"PATCH error: {response.text}")
                    break
            except Exception as e:
                print(f"PATCH request error: {e}")
                break

if __name__ == '__main__':
    test_complete_schedule_flow()