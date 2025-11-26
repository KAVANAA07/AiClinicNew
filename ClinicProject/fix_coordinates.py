#!/usr/bin/env python
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import Clinic

# Update ClinicX to your Mysore location
clinic = Clinic.objects.get(name="ClinicX")
clinic.latitude = 12.3508111
clinic.longitude = 76.6123884
clinic.save()
print(f"Updated {clinic.name} to Mysore coordinates: {clinic.latitude}, {clinic.longitude}")