#!/usr/bin/env python
import os
import sys
import django
from datetime import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Doctor, DoctorSchedule

def fix_schedules():
    print("Fixing existing schedules...")
    
    # Delete all existing schedules
    DoctorSchedule.objects.all().delete()
    print("Deleted all existing schedules")
    
    # Recreate schedules with proper time objects
    doctors = Doctor.objects.all()
    for doctor in doctors:
        schedule = DoctorSchedule.objects.create(
            doctor=doctor,
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration_minutes=15,
            is_active=True
        )
        print(f"Created schedule for {doctor.name}: {schedule.start_time} - {schedule.end_time}")
        
        # Test the get_total_slots method
        try:
            total_slots = schedule.get_total_slots()
            print(f"  Total slots: {total_slots}")
        except Exception as e:
            print(f"  Error calculating slots: {e}")

if __name__ == '__main__':
    fix_schedules()