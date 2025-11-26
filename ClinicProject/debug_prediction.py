#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.waiting_time_predictor import waiting_time_predictor
from api.models import Token, Doctor
from django.utils import timezone

print("=== PREDICTION DEBUG ===\n")

# Get a doctor
doctor = Doctor.objects.first()
if not doctor:
    print("No doctors found")
    exit()

print(f"Testing predictions for Dr. {doctor.name} (ID: {doctor.id})")

# Check current queue
current_queue = Token.objects.filter(
    doctor_id=doctor.id,
    created_at__date=timezone.now().date(),
    status__in=['waiting', 'confirmed', 'in_consultancy']
).order_by('appointment_time', 'created_at')

print(f"\nCurrent Queue Status:")
print(f"  Total in queue: {current_queue.count()}")
print(f"  In consultation: {current_queue.filter(status='in_consultancy').count()}")
print(f"  Waiting: {current_queue.filter(status='waiting').count()}")
print(f"  Confirmed: {current_queue.filter(status='confirmed').count()}")

# Test different scenarios
print(f"\nPrediction Tests:")

# Test 1: Empty queue
print(f"1. Empty queue prediction: {waiting_time_predictor.predict_waiting_time(doctor.id)}")

# Test 2: With appointment time
from datetime import time
test_time = time(14, 30)  # 2:30 PM
print(f"2. For 2:30 PM appointment: {waiting_time_predictor.predict_waiting_time(doctor.id, for_appointment_time=test_time)}")

# Test 3: Current queue analysis
if current_queue.exists():
    print(f"\n3. Current Queue Analysis:")
    for i, token in enumerate(current_queue[:5]):
        print(f"   Position {i+1}: Token {token.id}, Status: {token.status}, Time: {token.appointment_time or 'Walk-in'}")

# Test 4: Check if model is actually being used
print(f"\n4. Model Usage Check:")
print(f"   Model loaded: {waiting_time_predictor.load_model()}")
print(f"   Model path exists: {os.path.exists(waiting_time_predictor.model_path)}")

print(f"\n=== END DEBUG ===")