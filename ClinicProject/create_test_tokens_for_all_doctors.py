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
from api.models import Token, Doctor, Patient, Clinic
from django.utils import timezone
from datetime import time

def create_test_tokens_for_all_doctors():
    print("=== CREATING TEST TOKENS FOR ALL DOCTORS ===")
    
    doctors = Doctor.objects.filter(user__isnull=False)
    today = timezone.now().date()
    
    for doctor in doctors:
        print(f"\nCreating tokens for Doctor: {doctor.name} (User: {doctor.user.username})")
        
        # Create test patients for this doctor
        for i in range(3):
            patient_name = f"Test Patient {i+1} for {doctor.name}"
            patient, created = Patient.objects.get_or_create(
                name=patient_name,
                defaults={
                    'age': 25 + i * 10,
                    'phone_number': f'+123456789{doctor.id}{i}'
                }
            )
            
            # Create different types of tokens
            if i == 0:
                # Waiting token
                token = Token.objects.create(
                    patient=patient,
                    doctor=doctor,
                    clinic=doctor.clinic,
                    date=today,
                    status='waiting',
                    appointment_time=time(9, 0)
                )
                print(f"  Created waiting token: {token.id}")
                
            elif i == 1:
                # Confirmed token
                token = Token.objects.create(
                    patient=patient,
                    doctor=doctor,
                    clinic=doctor.clinic,
                    date=today,
                    status='confirmed',
                    appointment_time=time(10, 30)
                )
                print(f"  Created confirmed token: {token.id}")
                
            else:
                # Walk-in token (no appointment time)
                token = Token.objects.create(
                    patient=patient,
                    doctor=doctor,
                    clinic=doctor.clinic,
                    date=today,
                    status='confirmed'
                )
                print(f"  Created walk-in token: {token.id}")
    
    print(f"\nCompleted creating test tokens for {doctors.count()} doctors")
    
    # Show summary
    print("\n=== SUMMARY ===")
    for doctor in doctors:
        token_count = Token.objects.filter(doctor=doctor, date=today).exclude(status__in=['completed', 'cancelled']).count()
        print(f"Doctor {doctor.name}: {token_count} active tokens today")

if __name__ == "__main__":
    create_test_tokens_for_all_doctors()