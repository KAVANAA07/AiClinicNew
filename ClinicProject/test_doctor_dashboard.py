#!/usr/bin/env python
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Doctor, Patient, Token, Clinic
from django.utils import timezone
from datetime import time

def test_doctor_dashboard():
    print("Testing Doctor Dashboard Setup...")
    
    # Create test clinic
    clinic, _ = Clinic.objects.get_or_create(
        name="Test Clinic",
        defaults={
            'address': "123 Test St",
            'city': "Test City"
        }
    )
    
    # Create test doctor user
    doctor_user, created = User.objects.get_or_create(
        username="testdoctor",
        defaults={
            'password': 'testpass123',
            'is_staff': True
        }
    )
    if created:
        doctor_user.set_password('testpass123')
        doctor_user.save()
    
    # Create doctor profile
    doctor, _ = Doctor.objects.get_or_create(
        user=doctor_user,
        defaults={
            'name': "Dr. Test",
            'specialization': "General Medicine",
            'clinic': clinic
        }
    )
    
    # Create test patients and tokens
    for i in range(3):
        patient, _ = Patient.objects.get_or_create(
            name=f"Patient {i+1}",
            defaults={
                'age': 30 + i,
                'phone_number': f"+123456789{i}"
            }
        )
        
        # Create token for today
        token, _ = Token.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            date=timezone.now().date(),
            defaults={
                'status': 'waiting',
                'appointment_time': time(9 + i, 0) if i < 2 else None,
                'token_number': f"T{i+1}"
            }
        )
    
    print(f"✓ Created test data:")
    print(f"  - Clinic: {clinic.name}")
    print(f"  - Doctor: {doctor.name} (username: {doctor_user.username})")
    print(f"  - Tokens: {Token.objects.filter(doctor=doctor, date=timezone.now().date()).count()}")
    
    print(f"\n🌐 Access the doctor dashboard at:")
    print(f"   http://localhost:8000/api/doctor/dashboard/")
    print(f"\n📝 Login credentials:")
    print(f"   Username: testdoctor")
    print(f"   Password: testpass123")
    
    print(f"\n✨ Features available:")
    print(f"   - View patient queue")
    print(f"   - Start consultations")
    print(f"   - Add prescriptions with M/A/N timing")
    print(f"   - Custom timing and food instructions")
    print(f"   - SMS reminders for prescriptions")

if __name__ == "__main__":
    test_doctor_dashboard()