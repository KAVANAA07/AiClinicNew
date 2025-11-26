#!/usr/bin/env python
"""
Check and fix clinic coordinates for GPS confirmation
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import Clinic

def check_clinic_coordinates():
    """Check current clinic coordinates"""
    clinics = Clinic.objects.all()
    
    print("=== Current Clinic Coordinates ===")
    for clinic in clinics:
        print(f"Clinic: {clinic.name}")
        print(f"  Latitude: {clinic.latitude}")
        print(f"  Longitude: {clinic.longitude}")
        print(f"  Address: {clinic.address}")
        print()

def fix_clinic_coordinates():
    """Set sample coordinates for testing"""
    clinic = Clinic.objects.first()
    if clinic:
        # Set coordinates for a location in India (example: Mumbai)
        clinic.latitude = 19.0760
        clinic.longitude = 72.8777
        clinic.save()
        print(f"Updated {clinic.name} coordinates to Mumbai: {clinic.latitude}, {clinic.longitude}")
        return clinic
    return None

if __name__ == "__main__":
    check_clinic_coordinates()
    
    # Uncomment to fix coordinates:
    # fix_clinic_coordinates()
    # check_clinic_coordinates()