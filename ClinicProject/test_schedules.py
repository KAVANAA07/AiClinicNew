#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Doctor, Clinic, DoctorSchedule, Receptionist
from django.contrib.auth.models import User

def test_schedules():
    print("Testing Schedule Management...")
    
    # Check if we have any doctors
    doctors = Doctor.objects.all()
    print(f"Found {doctors.count()} doctors in database")
    
    for doctor in doctors:
        print(f"Doctor: {doctor.name} - Clinic: {doctor.clinic}")
        
        # Check if doctor has a schedule
        try:
            schedule = DoctorSchedule.objects.get(doctor=doctor)
            print(f"  Has schedule: {schedule.start_time} - {schedule.end_time}")
        except DoctorSchedule.DoesNotExist:
            print("  No schedule found, creating default...")
            from datetime import time
            schedule = DoctorSchedule.objects.create(
                doctor=doctor,
                start_time=time(9, 0),
                end_time=time(17, 0),
                slot_duration_minutes=15
            )
            print(f"  Created schedule: {schedule.start_time} - {schedule.end_time}")
    
    # Check receptionists
    receptionists = Receptionist.objects.all()
    print(f"\nFound {receptionists.count()} receptionists")
    
    for receptionist in receptionists:
        print(f"Receptionist: {receptionist.user.username} - Clinic: {receptionist.clinic}")

if __name__ == '__main__':
    test_schedules()