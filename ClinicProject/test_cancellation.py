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

def test_token_cancellation():
    print("=== Testing Token Cancellation Logic ===")
    
    # Get current time
    now = timezone.now()
    today = now.date()
    
    # Create a test appointment time that's 20 minutes ago (past the 15-minute grace period)
    past_time = (now - timedelta(minutes=20)).time()
    
    print(f"Current time: {now}")
    print(f"Test appointment time: {past_time} (20 minutes ago)")
    
    # Find tokens that should be cancelled
    missed_tokens = Token.objects.filter(
        date=today,
        appointment_time__isnull=False,
        status='waiting'
    )
    
    print(f"\nFound {missed_tokens.count()} waiting tokens for today:")
    for token in missed_tokens:
        appointment_datetime = datetime.combine(today, token.appointment_time)
        appointment_datetime_aware = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
        cutoff_time = appointment_datetime_aware + timedelta(minutes=15)
        
        is_past_due = now > cutoff_time
        print(f"  Token {token.id}: {token.patient.name} at {token.appointment_time} - {'PAST DUE' if is_past_due else 'NOT DUE'}")
    
    # Run the cancellation task
    print(f"\n=== Running Cancellation Task ===")
    result = check_and_cancel_missed_slots()
    print(f"Result: {result}")
    
    # Check what happened
    print(f"\n=== After Cancellation ===")
    cancelled_tokens = Token.objects.filter(
        date=today,
        status='cancelled'
    )
    
    print(f"Cancelled tokens: {cancelled_tokens.count()}")
    for token in cancelled_tokens:
        print(f"  Token {token.id}: {token.patient.name} - Status: {token.status}")

if __name__ == '__main__':
    test_token_cancellation()