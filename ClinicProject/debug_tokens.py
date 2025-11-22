#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Token, Doctor, Patient, Clinic
from django.utils import timezone

def debug_tokens():
    print("=== TOKEN DEBUG INFORMATION ===")
    
    # Check total tokens
    total_tokens = Token.objects.count()
    print(f"Total tokens in database: {total_tokens}")
    
    # Check today's tokens
    today = timezone.now().date()
    today_tokens = Token.objects.filter(date=today)
    print(f"Tokens for today ({today}): {today_tokens.count()}")
    
    # Check active tokens (not completed/cancelled)
    active_tokens = Token.objects.exclude(status__in=['completed', 'cancelled'])
    print(f"Active tokens: {active_tokens.count()}")
    
    # List all tokens with details
    print("\n=== ALL TOKENS ===")
    for token in Token.objects.all().order_by('-created_at')[:10]:  # Last 10 tokens
        print(f"Token ID: {token.id}")
        print(f"  Patient: {token.patient.name}")
        print(f"  Doctor: {token.doctor.name} (ID: {token.doctor.id})")
        print(f"  Clinic: {token.clinic.name if token.clinic else 'None'}")
        print(f"  Date: {token.date}")
        print(f"  Status: {token.status}")
        print(f"  Token Number: {token.token_number}")
        print(f"  Appointment Time: {token.appointment_time}")
        print("  ---")
    
    # Check doctors
    print("\n=== DOCTORS ===")
    for doctor in Doctor.objects.all():
        print(f"Doctor: {doctor.name} (ID: {doctor.id})")
        print(f"  User: {doctor.user.username if doctor.user else 'No user'}")
        print(f"  Clinic: {doctor.clinic.name if doctor.clinic else 'No clinic'}")
        doctor_tokens = Token.objects.filter(doctor=doctor, date=today)
        print(f"  Today's tokens: {doctor_tokens.count()}")
        print("  ---")
    
    # Check users with doctor profiles
    print("\n=== USERS WITH DOCTOR PROFILES ===")
    for user in User.objects.filter(doctor__isnull=False):
        print(f"User: {user.username}")
        print(f"  Doctor: {user.doctor.name}")
        print(f"  Is staff: {user.is_staff}")
        print(f"  Is active: {user.is_active}")
        print("  ---")

if __name__ == "__main__":
    debug_tokens()