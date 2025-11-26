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
from datetime import datetime, time

print("=== TREND ANALYSIS TEST ===\n")

doctor = Doctor.objects.first()
current_time = timezone.now()

print(f"Testing trend analysis for Dr. {doctor.name}")

# Test trend factor calculation
trend_factor = waiting_time_predictor.get_daily_trend_factor(doctor.id, current_time)
print(f"Current daily trend factor: {trend_factor:.2f}")

if trend_factor < 0.8:
    print("  -> Doctor is running FAST today (trend < 0.8)")
elif trend_factor > 1.2:
    print("  -> Doctor is running SLOW today (trend > 1.2)")
else:
    print("  -> Doctor is running NORMAL today (0.8 <= trend <= 1.2)")

# Show how predictions would change with different trends
base_prediction = 60  # Example base prediction

print(f"\nPrediction Examples (base: {base_prediction} min):")
for factor in [0.6, 0.8, 1.0, 1.2, 1.5]:
    adjusted = base_prediction * factor
    status = "FAST" if factor < 0.8 else "SLOW" if factor > 1.2 else "NORMAL"
    print(f"  Trend {factor:.1f} ({status}): {adjusted:.0f} minutes")

# Check today's completed consultations for trend analysis
today_completed = Token.objects.filter(
    doctor_id=doctor.id,
    date=current_time.date(),
    status='completed',
    completed_at__isnull=False
).count()

print(f"\nToday's Data:")
print(f"  Completed consultations: {today_completed}")
print(f"  Trend analysis {'ACTIVE' if today_completed >= 2 else 'INACTIVE (need 2+ consultations)'}")

print(f"\n=== END TEST ===")