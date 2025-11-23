#!/usr/bin/env python
"""
One-time cleanup of all expired tokens
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.utils import timezone
from datetime import datetime, timedelta
from api.models import Token

def cleanup_expired_tokens():
    """Cancel all expired tokens from previous days"""
    now = timezone.now()
    today = now.date()
    
    print("=== Cleaning Up Expired Tokens ===")
    
    # Find all waiting tokens from before today
    expired_tokens = Token.objects.filter(
        date__lt=today,
        status='waiting'
    )
    
    count = expired_tokens.count()
    print(f"Found {count} expired tokens from previous days")
    
    if count == 0:
        print("No expired tokens to clean up")
        return
    
    # Show what will be cancelled
    for token in expired_tokens:
        print(f"  - {token.patient.name}: {token.date} at {token.appointment_time or 'No time'} (Token {token.id})")
    
    # Cancel them all
    updated = expired_tokens.update(status='cancelled')
    print(f"\n[OK] Cancelled {updated} expired tokens")
    
    # Also check for any tokens from today that are clearly expired
    today_expired = Token.objects.filter(
        date=today,
        appointment_time__isnull=False,
        status='waiting'
    )
    
    grace_period = timedelta(minutes=15)
    today_cancelled = 0
    
    for token in today_expired:
        appointment_datetime = datetime.combine(token.date, token.appointment_time)
        appointment_datetime_aware = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
        cutoff_time = appointment_datetime_aware + grace_period
        
        if now > cutoff_time:
            token.status = 'cancelled'
            token.save()
            today_cancelled += 1
            print(f"  - Today expired: {token.patient.name} at {token.appointment_time.strftime('%I:%M %p')}")
    
    if today_cancelled > 0:
        print(f"[OK] Also cancelled {today_cancelled} expired tokens from today")
    
    total_cancelled = updated + today_cancelled
    print(f"\nTotal tokens cancelled: {total_cancelled}")
    print("Cleanup complete!")

if __name__ == '__main__':
    cleanup_expired_tokens()