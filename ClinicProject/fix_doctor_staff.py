#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Doctor

def fix_doctor_staff_status():
    print("=== FIXING DOCTOR STAFF STATUS ===")
    
    doctors = Doctor.objects.filter(user__isnull=False)
    
    for doctor in doctors:
        user = doctor.user
        print(f"Doctor: {doctor.name} (User: {user.username})")
        print(f"  Before - is_staff: {user.is_staff}")
        
        # Make the user a staff member
        user.is_staff = True
        user.save()
        
        print(f"  After - is_staff: {user.is_staff}")
        print("  ---")
    
    print(f"Updated {doctors.count()} doctor users to be staff members")

if __name__ == "__main__":
    fix_doctor_staff_status()