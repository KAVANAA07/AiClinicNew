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

def update_clinic_coordinates():
    print("=== GET ACCURATE CLINIC COORDINATES ===")
    print()
    
    # Show current clinic
    clinic = Clinic.objects.filter(name="ClinicX").first()
    if clinic:
        print(f"Current clinic: {clinic.name}")
        print(f"Current coordinates: {clinic.latitude}, {clinic.longitude}")
        print()
    
    print("HOW TO GET ACCURATE COORDINATES:")
    print()
    print("METHOD 1 - Google Maps (Most Accurate):")
    print("1. Go to https://maps.google.com")
    print("2. Search for your clinic address")
    print("3. Right-click on the exact clinic location")
    print("4. Click on the coordinates that appear (e.g., '12.901088, 74.987157')")
    print("5. Copy the coordinates")
    print()
    
    print("METHOD 2 - Phone GPS:")
    print("1. Stand at your clinic entrance")
    print("2. Open GPS app or Google Maps")
    print("3. Long press on your current location")
    print("4. Copy the coordinates shown")
    print()
    
    print("METHOD 3 - Address to Coordinates:")
    print("1. Go to https://www.latlong.net/")
    print("2. Enter your clinic's full address")
    print("3. Click 'Find' to get coordinates")
    print()
    
    print("ENTER YOUR CLINIC'S ACCURATE COORDINATES:")
    print("Format: latitude,longitude (e.g., 12.901088,74.987157)")
    print()
    
    try:
        coords_input = input("Enter coordinates (or press Enter to skip): ").strip()
        
        if coords_input:
            # Parse coordinates
            if ',' in coords_input:
                lat_str, lon_str = coords_input.split(',')
                latitude = float(lat_str.strip())
                longitude = float(lon_str.strip())
                
                # Validate coordinates
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    # Update clinic
                    if clinic:
                        clinic.latitude = latitude
                        clinic.longitude = longitude
                        clinic.save()
                        print(f"✓ Updated {clinic.name} coordinates to: {latitude}, {longitude}")
                        
                        # Test distance calculation
                        from math import radians, sin, cos, sqrt, atan2
                        
                        def haversine_distance(lat1, lon1, lat2, lon2):
                            R = 6371.0
                            lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
                            dlon, dlat = lon2_rad - lon1_rad, lat2_rad - lat1_rad
                            a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
                            return R * (2 * atan2(sqrt(a), sqrt(1 - a)))
                        
                        # Test with same coordinates
                        distance = haversine_distance(latitude, longitude, latitude, longitude)
                        print(f"✓ Test distance (same location): {distance:.3f} km")
                        
                        # Test with nearby location (100m away)
                        test_lat = latitude + 0.001
                        test_lon = longitude + 0.001
                        distance = haversine_distance(latitude, longitude, test_lat, test_lon)
                        print(f"✓ Test distance (100m away): {distance:.3f} km")
                        
                        print()
                        print("COORDINATES UPDATED SUCCESSFULLY!")
                        print("Now restart your Django server and try arrival confirmation again.")
                        
                    else:
                        print("❌ No clinic found to update")
                else:
                    print("❌ Invalid coordinates. Latitude must be -90 to 90, longitude -180 to 180")
            else:
                print("❌ Invalid format. Use: latitude,longitude")
        else:
            print("Skipped coordinate update")
            
    except ValueError:
        print("❌ Invalid coordinate format. Use numbers only.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_clinic_coordinates()