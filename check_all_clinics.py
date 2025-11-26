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

def check_all_clinics():
    print("=== ALL CLINICS COORDINATES ===")
    
    clinics = Clinic.objects.all()
    
    for i, clinic in enumerate(clinics, 1):
        print(f"{i}. {clinic.name}")
        print(f"   Latitude: {clinic.latitude}")
        print(f"   Longitude: {clinic.longitude}")
        
        if clinic.latitude and clinic.longitude:
            # Check if coordinates look swapped
            if clinic.latitude > clinic.longitude and clinic.latitude > 50:
                print("   STATUS: COORDINATES APPEAR SWAPPED!")
                
                # Fix them
                old_lat = clinic.latitude
                old_lon = clinic.longitude
                
                clinic.latitude = old_lon
                clinic.longitude = old_lat
                clinic.save()
                
                print(f"   FIXED: lat={clinic.latitude}, lon={clinic.longitude}")
            else:
                print("   STATUS: Coordinates look correct")
        else:
            print("   STATUS: No coordinates set")
        print()

if __name__ == "__main__":
    check_all_clinics()