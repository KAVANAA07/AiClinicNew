#!/usr/bin/env python
"""
Set clinic coordinates to your test location
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import Clinic

def set_clinic_to_location(lat, lng, clinic_name="ClinicX"):
    """Set clinic coordinates to your location"""
    try:
        clinic = Clinic.objects.get(name=clinic_name)
        clinic.latitude = lat
        clinic.longitude = lng
        clinic.save()
        print(f"Updated {clinic.name} coordinates to: {lat}, {lng}")
        return True
    except Clinic.DoesNotExist:
        print(f"Clinic {clinic_name} not found")
        return False

if __name__ == "__main__":
    # Example: Set to your current location
    # Replace these with your actual coordinates from Google Maps
    your_lat = 12.901000  # Replace with your latitude
    your_lng = 74.988000  # Replace with your longitude
    
    print("Setting clinic coordinates to test location...")
    success = set_clinic_to_location(your_lat, your_lng)
    
    if success:
        print("Now try GPS confirmation - it should work!")
    else:
        print("Failed to update coordinates")