#!/usr/bin/env python3

import os
import sys
import django

sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Clinic

def update_coordinates():
    print("=== UPDATE CLINIC COORDINATES ===")
    
    clinic = Clinic.objects.filter(name="ClinicX").first()
    if not clinic:
        print("No ClinicX found!")
        return
    
    print(f"Current: {clinic.latitude}, {clinic.longitude}")
    print()
    print("EASY WAYS TO GET COORDINATES:")
    print("1. Google Maps: Right-click on clinic location -> Copy coordinates")
    print("2. GPS app: Stand at clinic -> Copy coordinates")
    print("3. Address lookup: https://www.latlong.net/")
    print()
    
    # Example coordinates for common Indian cities
    examples = {
        "Bangalore": "12.9716, 77.5946",
        "Mumbai": "19.0760, 72.8777", 
        "Delhi": "28.6139, 77.2090",
        "Chennai": "13.0827, 80.2707",
        "Hyderabad": "17.3850, 78.4867"
    }
    
    print("EXAMPLE COORDINATES:")
    for city, coords in examples.items():
        print(f"  {city}: {coords}")
    print()
    
    coords = input("Enter coordinates (latitude,longitude) or press Enter to skip: ").strip()
    
    if coords and ',' in coords:
        try:
            lat_str, lon_str = coords.split(',')
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())
            
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                clinic.latitude = lat
                clinic.longitude = lon
                clinic.save()
                print(f"Updated to: {lat}, {lon}")
                
                # Test distance
                from math import radians, sin, cos, sqrt, atan2
                def haversine_distance(lat1, lon1, lat2, lon2):
                    R = 6371.0
                    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
                    dlon, dlat = lon2_rad - lon1_rad, lat2_rad - lat1_rad
                    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
                    return R * (2 * atan2(sqrt(a), sqrt(1 - a)))
                
                # Test nearby location
                test_lat = lat + 0.001
                test_lon = lon + 0.001
                distance = haversine_distance(lat, lon, test_lat, test_lon)
                print(f"Test distance (100m away): {distance:.3f}km")
                print("Coordinates updated successfully!")
            else:
                print("Invalid coordinates")
        except ValueError:
            print("Invalid format")
    else:
        print("Skipped")

if __name__ == "__main__":
    update_coordinates()