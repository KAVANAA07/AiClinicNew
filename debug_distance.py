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

def debug_your_location():
    print("=== GPS DISTANCE DEBUGGING ===")
    
    # Get clinic coordinates
    clinic = Clinic.objects.filter(latitude__isnull=False, longitude__isnull=False).first()
    if not clinic:
        print("ERROR: No clinic with GPS coordinates found!")
        return
    
    print(f"Clinic: {clinic.name}")
    print(f"Clinic coordinates: {clinic.latitude}, {clinic.longitude}")
    print()
    
    # REPLACE THESE WITH YOUR ACTUAL GPS COORDINATES
    print("PLEASE REPLACE THESE COORDINATES WITH YOUR ACTUAL LOCATION:")
    print("Get your coordinates from:")
    print("1. Google Maps - Right click on your location and copy coordinates")
    print("2. Your phone's GPS app")
    print("3. GPS coordinate websites")
    print()
    
    # TEST COORDINATES - REPLACE THESE WITH YOUR ACTUAL LOCATION
    your_latitude = 12.901088   # REPLACE WITH YOUR ACTUAL LATITUDE
    your_longitude = 74.987157  # REPLACE WITH YOUR ACTUAL LONGITUDE
    
    print(f"Your test coordinates: {your_latitude}, {your_longitude}")
    print()
    
    # Calculate distance
    distance = haversine_distance(clinic.latitude, clinic.longitude, your_latitude, your_longitude)
    
    print(f"Distance from clinic: {distance:.3f} km")
    print(f"Current limit: 10.0 km (temporarily increased)")
    print(f"Status: {'ALLOWED' if distance <= 10.0 else 'BLOCKED'}")
    print()
    
    if distance > 10.0:
        print("ISSUE FOUND:")
        print(f"Your location is {distance:.1f}km away from the clinic")
        print("This is more than the 10km temporary limit")
        print()
        print("SOLUTIONS:")
        print("1. Update clinic coordinates in Django admin to match actual clinic location")
        print("2. Use your actual GPS coordinates (not test coordinates)")
        print("3. Temporarily increase distance limit further for testing")
        print("4. Check if latitude/longitude are swapped")
    else:
        print("GPS distance check should work!")
        print("If still not working, check:")
        print("1. Are you sending the correct coordinates from your app?")
        print("2. Is the server running the updated code?")
        print("3. Check browser console for any errors")

if __name__ == "__main__":
    debug_your_location()