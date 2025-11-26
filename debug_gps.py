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

def debug_gps_issue():
    print("=== GPS Distance Debugging ===")
    
    # Get all clinics with GPS coordinates
    clinics = Clinic.objects.filter(latitude__isnull=False, longitude__isnull=False)
    
    if not clinics.exists():
        print("ERROR: No clinics found with GPS coordinates!")
        print("Please add latitude and longitude to your clinic in Django admin.")
        return
    
    for clinic in clinics:
        print(f"\nClinic: {clinic.name}")
        print(f"Coordinates: {clinic.latitude}, {clinic.longitude}")
        
        # Test with some sample user coordinates (you can replace these with your actual coordinates)
        test_coordinates = [
            (clinic.latitude, clinic.longitude),  # Exact same location
            (clinic.latitude + 0.001, clinic.longitude + 0.001),  # ~100m away
            (clinic.latitude + 0.01, clinic.longitude + 0.01),   # ~1km away
            (clinic.latitude + 0.1, clinic.longitude + 0.1),     # ~10km away
        ]
        
        for i, (user_lat, user_lon) in enumerate(test_coordinates):
            distance = haversine_distance(clinic.latitude, clinic.longitude, user_lat, user_lon)
            status = "ALLOWED" if distance <= 1.0 else "BLOCKED"
            print(f"  Test {i+1}: User at ({user_lat:.6f}, {user_lon:.6f}) = {distance:.3f}km {status}")
    
    print("\n=== Your GPS Coordinates Test ===")
    print("Please provide your actual GPS coordinates to test:")
    print("You can get them from your phone's GPS or Google Maps")
    
    # If you want to test with specific coordinates, uncomment and modify these lines:
    # your_lat = 12.9716  # Replace with your latitude
    # your_lon = 77.5946  # Replace with your longitude
    # 
    # for clinic in clinics:
    #     distance = haversine_distance(clinic.latitude, clinic.longitude, your_lat, your_lon)
    #     status = "ALLOWED" if distance <= 1.0 else "BLOCKED"
    #     print(f"Your location to {clinic.name}: {distance:.3f}km {status}")

if __name__ == "__main__":
    debug_gps_issue()