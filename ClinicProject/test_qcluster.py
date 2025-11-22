#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django_q.models import Schedule, Task
from api.tasks import check_and_cancel_missed_slots

def test_qcluster():
    print("=== Django-Q Cluster Test ===")
    
    # Check if schedules exist
    schedules = Schedule.objects.all()
    print(f"Found {schedules.count()} scheduled tasks:")
    for schedule in schedules:
        print(f"  - {schedule.name}: {schedule.func} (every {schedule.minutes} minutes)")
    
    # Test the task function directly
    print("\n=== Testing missed appointment checker ===")
    try:
        result = check_and_cancel_missed_slots()
        print(f"Task result: {result}")
    except Exception as e:
        print(f"Task error: {e}")
    
    # Check recent task executions
    recent_tasks = Task.objects.filter(func='api.tasks.check_and_cancel_missed_slots').order_by('-started')[:5]
    print(f"\nRecent task executions ({recent_tasks.count()}):")
    for task in recent_tasks:
        print(f"  - {task.started}: {task.success} ({task.result})")

if __name__ == '__main__':
    test_qcluster()