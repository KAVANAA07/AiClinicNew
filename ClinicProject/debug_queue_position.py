#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Doctor
from django.utils import timezone
from datetime import time

print("=== QUEUE POSITION DEBUG ===\n")

doctor = Doctor.objects.first()
current_time = timezone.now()

print(f"Doctor: {doctor.name}")
print(f"Current time: {current_time}")
print(f"Current date: {current_time.date()}")

# Get current active queue
current_queue = Token.objects.filter(
    doctor_id=doctor.id,
    created_at__date=current_time.date(),
    status__in=['waiting', 'confirmed', 'in_consultancy']
).order_by('appointment_time', 'created_at')

print(f"\nCurrent Queue ({current_queue.count()} tokens):")
for i, token in enumerate(current_queue):
    print(f"  {i+1}. Token {token.id}: {token.status}, Time: {token.appointment_time}, Created: {token.created_at}")

# Test appointment time scenarios
test_time = time(14, 30)  # 2:30 PM
print(f"\nTesting appointment at {test_time}:")

patients_before = current_queue.filter(
    appointment_time__lt=test_time
).count()

print(f"  Patients with appointments before {test_time}: {patients_before}")
print(f"  Queue position would be: {patients_before + 1}")

# Test walk-in scenario
queue_count = current_queue.count()
print(f"\nWalk-in scenario:")
print(f"  Current queue count: {queue_count}")
print(f"  Walk-in position would be: {queue_count + 1}")

print(f"\n=== END DEBUG ===")