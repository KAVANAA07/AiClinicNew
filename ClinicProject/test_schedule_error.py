#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import DoctorSchedule, Doctor
from api.serializers import DoctorScheduleSerializer

try:
    # Test creating a schedule
    doctor = Doctor.objects.first()
    if doctor:
        schedule = DoctorSchedule.objects.create(
            doctor=doctor,
            start_time='09:00',
            end_time='17:00',
            slot_duration_minutes=15
        )
        print(f"Created schedule: {schedule}")
        
        # Test serializing
        serializer = DoctorScheduleSerializer(schedule)
        print(f"Serialized data: {serializer.data}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()