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

def set_doctor_passwords():
    print("=== SETTING DOCTOR PASSWORDS ===")
    
    doctors = Doctor.objects.filter(user__isnull=False)
    
    for doctor in doctors:
        user = doctor.user
        print(f"Doctor: {doctor.name} (User: {user.username})")
        
        # Set password to 'password123'
        user.set_password('password123')
        user.save()
        
        print(f"  Password set to 'password123'")
        print("  ---")
    
    print(f"Updated passwords for {doctors.count()} doctor users")

if __name__ == "__main__":
    set_doctor_passwords()