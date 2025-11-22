#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import State, District, Clinic, Doctor

# Check and create required data
print("Checking IVR data...")

# Create state if missing
if not State.objects.exists():
    state = State.objects.create(name="Karnataka")
    print("Created state: Karnataka")
else:
    state = State.objects.first()
    print(f"State exists: {state.name}")

# Create district if missing
if not District.objects.exists():
    district = District.objects.create(name="Dakshina Kannada", state=state)
    print("Created district: Dakshina Kannada")
else:
    district = District.objects.first()
    print(f"District exists: {district.name}")

# Create clinic if missing
if not Clinic.objects.exists():
    clinic = Clinic.objects.create(
        name="Test Clinic",
        district=district,
        address="Test Address",
        phone_number="+1234567890"
    )
    print("Created clinic: Test Clinic")
else:
    clinic = Clinic.objects.first()
    print(f"Clinic exists: {clinic.name}")

# Create doctor if missing
if not Doctor.objects.exists():
    doctor = Doctor.objects.create(
        name="Dr. Test",
        specialization="General",
        clinic=clinic
    )
    print("Created doctor: Dr. Test")
else:
    doctor = Doctor.objects.first()
    print(f"Doctor exists: {doctor.name}")

print("\nIVR data setup complete!")
print("Now test your IVR call again.")