import os
import sys
import django

sys.path.append('c:/Users/VITUS/AiClinicNew/ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Doctor, Patient
from django.utils import timezone
from datetime import datetime, timedelta, time
import random

print("="*70)
print("GENERATING SYNTHETIC TRAINING DATA")
print("="*70)

# Get existing completed tokens
completed_tokens = Token.objects.filter(status='completed')
print(f"\nFound {completed_tokens.count()} completed tokens")

# Fix existing tokens by adding missing fields
fixed_count = 0
for token in completed_tokens:
    needs_update = False
    
    # Add appointment_time if missing
    if not token.appointment_time:
        # Generate unique appointment time using created_at
        created_hour = token.created_at.hour if token.created_at else 10
        created_minute = token.created_at.minute if token.created_at else 0
        # Round to nearest 15 minutes
        minute = (created_minute // 15) * 15
        token.appointment_time = time(created_hour, minute)
        needs_update = True
    
    # Add consultation_start_time if missing
    if not token.consultation_start_time:
        # Set consultation start time slightly after appointment
        if token.created_at:
            # Use created_at as base
            delay_minutes = random.randint(0, 10)
            token.consultation_start_time = token.created_at + timedelta(minutes=delay_minutes)
        else:
            appointment_dt = timezone.make_aware(
                datetime.combine(token.date, token.appointment_time)
            )
            delay_minutes = random.randint(0, 10)
            token.consultation_start_time = appointment_dt + timedelta(minutes=delay_minutes)
        needs_update = True
    
    # Add completed_at if missing
    if not token.completed_at:
        # Set completion time 10-25 minutes after consultation start
        consultation_duration = random.randint(10, 25)
        token.completed_at = token.consultation_start_time + timedelta(minutes=consultation_duration)
        needs_update = True
    
    if needs_update:
        try:
            token.save()
            fixed_count += 1
        except Exception as e:
            print(f"Skipping token {token.id}: {e}")
            continue

print(f"Fixed {fixed_count} tokens with missing data")

# Verify the fix
valid_tokens = Token.objects.filter(
    status='completed',
    completed_at__isnull=False,
    appointment_time__isnull=False,
    consultation_start_time__isnull=False
).count()

print(f"\nValid tokens after fix: {valid_tokens}")

if valid_tokens >= 50:
    print("\nSUCCESS: You now have enough data to train the model!")
    print("Run: python manage.py evaluate_model")
else:
    print(f"\nWARNING: Still need more data ({valid_tokens}/50)")

print("\n" + "="*70)
