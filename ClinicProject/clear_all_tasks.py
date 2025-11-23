#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django_q.models import Schedule, Task

# Delete ALL schedules and tasks
Schedule.objects.all().delete()
Task.objects.all().delete()

# Create new schedule
Schedule.objects.create(
    name='check_missed_appointments',
    func='api.tasks.check_and_cancel_missed_slots',
    schedule_type=Schedule.MINUTES,
    minutes=5,
    repeats=-1
)

print("Cleared all tasks and schedules. Created new schedule.")
print("Restart qcluster now.")