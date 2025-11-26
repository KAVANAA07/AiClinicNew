#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Clinic

def fix_clinic_coordinates():
    print("=== FIXING CLINIC COORDINATES ===")
    
    clinic = Clinic.objects.first()
    if not clinic:
        print("ERROR: No clinic found!")
        return
    
    print(f"Clinic: {clinic.name}")
    print(f"Current coordinates: {clinic.latitude}, {clinic.longitude}")
    
    # The coordinates appear to be swapped
    # Current: latitude=74.987157, longitude=12.901088
    # Should be: latitude=12.901088, longitude=74.987157
    
    if clinic.latitude > 90 or clinic.latitude < -90:
        print("ERROR: Invalid latitude detected!")
        print("Latitude must be between -90 and 90")
        return
    
    if clinic.longitude > 180 or clinic.longitude < -180:
        print("ERROR: Invalid longitude detected!")
        print("Longitude must be between -180 and 180")
        return
    
    # Check if coordinates look swapped (latitude > longitude in India)
    if clinic.latitude > clinic.longitude and clinic.latitude > 50:
        print("COORDINATES APPEAR TO BE SWAPPED!")
        print(f"Current: lat={clinic.latitude}, lon={clinic.longitude}")
        
        # Swap them
        old_lat = clinic.latitude
        old_lon = clinic.longitude
        
        clinic.latitude = old_lon
        clinic.longitude = old_lat
        clinic.save()
        
        print(f"Fixed:   lat={clinic.latitude}, lon={clinic.longitude}")
        print("Coordinates have been swapped and saved!")
        
        # Test the distance now
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371.0
            lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
            dlon, dlat = lon2_rad - lon1_rad, lat2_rad - lat1_rad
            a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
            return R * (2 * atan2(sqrt(a), sqrt(1 - a)))
        
        # Test with same coordinates (should be 0km)
        distance = haversine_distance(clinic.latitude, clinic.longitude, clinic.latitude, clinic.longitude)
        print(f"Test distance (same location): {distance:.3f} km")
        
        # Test with nearby coordinates
        test_lat = clinic.latitude + 0.001
        test_lon = clinic.longitude + 0.001
        distance = haversine_distance(clinic.latitude, clinic.longitude, test_lat, test_lon)
        print(f"Test distance (100m away): {distance:.3f} km")
        
    else:
        print("Coordinates appear to be in correct order")
        print("The issue might be elsewhere")

if __name__ == "__main__":
    fix_clinic_coordinates()