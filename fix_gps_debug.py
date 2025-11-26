#!/usr/bin/env python3

import os
import sys
import django
from math import radians, sin, cos, sqrt, atan2

# Add the project directory to Python path
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Clinic

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates"""
    R = 6371.0  # Radius of Earth in kilometers
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlon, dlat = lon2_rad - lon1_rad, lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    return R * (2 * atan2(sqrt(a), sqrt(1 - a)))

def test_your_coordinates():
    print("=== GPS DEBUGGING FOR YOUR LOCATION ===")
    
    # Get clinic coordinates
    clinic = Clinic.objects.filter(latitude__isnull=False, longitude__isnull=False).first()
    if not clinic:
        print("ERROR: No clinic with GPS coordinates found!")
        return
    
    print(f"Clinic: {clinic.name}")
    print(f"Clinic coordinates: {clinic.latitude}, {clinic.longitude}")
    print()
    
    # Test with your coordinates (REPLACE THESE WITH YOUR ACTUAL COORDINATES)
    print("PLEASE REPLACE THESE WITH YOUR ACTUAL GPS COORDINATES:")
    print("You can get them from:")
    print("1. Google Maps - Right click on your location")
    print("2. Your phone's GPS app")
    print("3. GPS coordinate apps")
    print()
    
    # REPLACE THESE COORDINATES WITH YOUR ACTUAL LOCATION
    your_latitude = 12.901088   # REPLACE THIS
    your_longitude = 74.987157  # REPLACE THIS
    
    print(f"Your coordinates (CHANGE THESE): {your_latitude}, {your_longitude}")
    
    # Test normal order
    distance1 = haversine_distance(clinic.latitude, clinic.longitude, your_latitude, your_longitude)
    print(f"Distance (lat,lon): {distance1:.3f}km - {'ALLOWED' if distance1 <= 1.0 else 'BLOCKED'}")
    
    # Test swapped coordinates (common mistake)
    distance2 = haversine_distance(clinic.latitude, clinic.longitude, your_longitude, your_latitude)
    print(f"Distance (lon,lat): {distance2:.3f}km - {'ALLOWED' if distance2 <= 1.0 else 'BLOCKED'}")
    
    print()
    print("SOLUTIONS:")
    print("1. Make sure clinic coordinates are correct in Django admin")
    print("2. Use precise GPS coordinates from your phone")
    print("3. Check if lat/lon are swapped in your app")
    print("4. Temporarily increase the distance limit for testing")

def update_clinic_coordinates():
    """Helper to update clinic coordinates"""
    print("=== UPDATE CLINIC COORDINATES ===")
    clinic = Clinic.objects.first()
    if clinic:
        print(f"Current clinic: {clinic.name}")
        print(f"Current coordinates: {clinic.latitude}, {clinic.longitude}")
        print()
        print("To update coordinates:")
        print("1. Go to Django admin: http://localhost:8000/admin/")
        print("2. Go to Clinics section")
        print("3. Edit your clinic")
        print("4. Update latitude and longitude fields")
        print("5. Save changes")

if __name__ == "__main__":
    test_your_coordinates()
    print()
    update_clinic_coordinates()