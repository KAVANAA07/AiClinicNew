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

def test_clinic_coordinates():
    print("=== TESTING CLINIC COORDINATES ===")
    
    clinics = Clinic.objects.filter(latitude__isnull=False, longitude__isnull=False)
    
    if not clinics.exists():
        print("No clinics with coordinates found!")
        print("Please add coordinates using Django admin at: http://localhost:8000/admin/")
        return
    
    for clinic in clinics:
        print(f"\nClinic: {clinic.name}")
        print(f"Coordinates: {clinic.latitude}, {clinic.longitude}")
        print(f"Google Maps: https://maps.google.com/maps?q={clinic.latitude},{clinic.longitude}")
        
        # Test distances
        test_locations = [
            ("Same location", clinic.latitude, clinic.longitude),
            ("100m away", clinic.latitude + 0.001, clinic.longitude + 0.001),
            ("500m away", clinic.latitude + 0.005, clinic.longitude + 0.005),
            ("1km away", clinic.latitude + 0.01, clinic.longitude + 0.01),
            ("2km away", clinic.latitude + 0.02, clinic.longitude + 0.02),
        ]
        
        print("\nDistance tests:")
        for name, test_lat, test_lon in test_locations:
            distance = haversine_distance(clinic.latitude, clinic.longitude, test_lat, test_lon)
            status = "ALLOWED" if distance <= 1.0 else "BLOCKED"
            print(f"  {name}: {distance:.3f}km - {status}")

if __name__ == "__main__":
    test_clinic_coordinates()