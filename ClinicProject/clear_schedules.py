#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import DoctorSchedule

# Delete all schedules to clear any corrupted data
DoctorSchedule.objects.all().delete()
print("All schedules cleared")