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

def create_and_test():
    print("Creating test token with past appointment time...")
    
    now = timezone.now()
    today = now.date()
    past_time = (now - timedelta(minutes=30)).time()
    
    # Get first available patient, doctor, clinic
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()
    clinic = Clinic.objects.first()
    
    if not all([patient, doctor, clinic]):
        print("ERROR: Need at least one Patient, Doctor, and Clinic in database")
        return
    
    # Create test token
    token = Token.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        date=today,
        appointment_time=past_time,
        status='waiting',
        token_number=f'DEMO-{now.strftime("%H%M%S")}'
    )
    
    print(f"Created token {token.id} for {patient.name} at {past_time}")
    print("\\nRunning cancellation check...")
    
    # Run cancellation
    result = check_and_cancel_missed_slots()

if __name__ == '__main__':
    create_and_test()