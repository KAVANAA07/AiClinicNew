#!/usr/bin/env python
import os
import django
from django.conf import settings
from datetime import datetime, time, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Patient, Doctor, Clinic
from api.tasks import check_and_cancel_missed_slots

def test_cancellation():
    print("=== Testing Token Cancellation ===")
    
    now = timezone.now()
    today = now.date()
    
    # Check for waiting tokens
    waiting_tokens = Token.objects.filter(
        date=today,
        status='waiting',
        appointment_time__isnull=False
    )
    
    print(f"Found {waiting_tokens.count()} waiting tokens:")
    for token in waiting_tokens:
        appointment_datetime = datetime.combine(today, token.appointment_time)
        appointment_datetime_aware = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
        cutoff_time = appointment_datetime_aware + timedelta(minutes=15)
        is_past_due = now > cutoff_time
        
        print(f"  Token {token.id}: {token.patient.name} at {token.appointment_time}")
        print(f"    Appointment: {appointment_datetime_aware}")
        print(f"    Cutoff: {cutoff_time}")
        print(f"    Current: {now}")
        print(f"    Past due: {is_past_due}")
        print()
    
    # Run cancellation
    print("Running cancellation task...")
    result = check_and_cancel_missed_slots()
    print(f"Result: {result}")
    
    # Check status after
    print("\nAfter cancellation:")
    updated_tokens = Token.objects.filter(
        date=today,
        appointment_time__isnull=False
    ).order_by('appointment_time')
    
    for token in updated_tokens:
        print(f"  Token {token.id}: {token.patient.name} - {token.status} - {token.appointment_time}")

if __name__ == '__main__':
    test_cancellation()