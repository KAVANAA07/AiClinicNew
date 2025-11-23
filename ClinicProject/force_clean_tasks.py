#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django_q.models import Schedule, Task

print("=== Force Cleaning All Django-Q Data ===")

# Delete ALL tasks and schedules
tasks_deleted = Task.objects.all().delete()[0]
schedules_deleted = Schedule.objects.all().delete()[0]

print(f"Deleted {tasks_deleted} tasks")
print(f"Deleted {schedules_deleted} schedules")

# Create correct schedule
schedule = Schedule.objects.create(
    name='check_missed_appointments',
    func='api.tasks.check_and_cancel_missed_slots',
    schedule_type=Schedule.MINUTES,
    minutes=5,
    repeats=-1
)

print(f"Created schedule: {schedule.name} -> {schedule.func}")

# Verify no old tasks exist
remaining_tasks = Task.objects.count()
remaining_schedules = Schedule.objects.count()

print(f"Remaining tasks: {remaining_tasks}")
print(f"Remaining schedules: {remaining_schedules}")

print("\n=== STOP qcluster NOW and restart it ===")
print("1. Press Ctrl+C to stop qcluster")
print("2. Run: python manage.py qcluster")