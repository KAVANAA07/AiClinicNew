#!/usr/bin/env python
"""
Test script to demonstrate receptionist token confirmation functionality.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import Token, Receptionist, Patient, Doctor
from django.contrib.auth.models import User
from django.utils import timezone

def create_test_token():
    """Create a test token for demonstration"""
    try:
        # Find a receptionist and their clinic
        receptionist_user = User.objects.filter(receptionist__isnull=False).first()
        if not receptionist_user:
            print("[ERROR] No receptionist found")
            return None
            
        receptionist = receptionist_user.receptionist
        clinic = receptionist.clinic
        
        # Find a doctor in the same clinic
        doctor = Doctor.objects.filter(clinic=clinic).first()
        if not doctor:
            print("[ERROR] No doctor found in clinic")
            return None
            
        # Find or create a test patient
        patient, created = Patient.objects.get_or_create(
            phone_number="+1234567890",
            defaults={
                'name': 'Test Patient',
                'age': 30
            }
        )
        
        # Create a test token
        token = Token.objects.create(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            date=timezone.now().date(),
            status='waiting'
        )
        
        print(f"[SUCCESS] Created test token {token.id}")
        print(f"   Patient: {patient.name}")
        print(f"   Doctor: {doctor.name}")
        print(f"   Clinic: {clinic.name}")
        print(f"   Status: {token.status}")
        
        return token
        
    except Exception as e:
        print(f"[ERROR] Failed to create test token: {str(e)}")
        return None

def test_receptionist_confirmation(token):
    """Test the receptionist confirmation process"""
    try:
        print(f"\n=== Testing Receptionist Confirmation for Token {token.id} ===")
        
        # Simulate what the ReceptionistConfirmArrivalView does
        original_status = token.status
        print(f"[INFO] Original status: {original_status}")
        
        # Manual confirmation by receptionist
        token.status = 'confirmed'
        token.arrival_confirmed_at = timezone.now()
        token._manual_confirmation_allowed = True  # This is the key flag
        token.save()
        
        # Verify the change
        token.refresh_from_db()
        print(f"[INFO] New status: {token.status}")
        print(f"[INFO] Confirmed at: {token.arrival_confirmed_at}")
        
        if token.status == 'confirmed':
            print("[SUCCESS] Token successfully confirmed by receptionist!")
            return True
        else:
            print("[ERROR] Token confirmation failed!")
            return False
            
    except Exception as e:
        print(f"[ERROR] Confirmation test failed: {str(e)}")
        return False

def show_api_usage():
    """Show how to use the API endpoints"""
    print("\n=== API Usage Examples ===")
    print("1. Receptionist confirms token arrival:")
    print("   POST /api/tokens/{token_id}/receptionist-confirm/")
    print("   Headers: Authorization: Token {receptionist_auth_token}")
    print("   Body: {} (empty)")
    print()
    print("2. Update token status directly:")
    print("   PATCH /api/tokens/{token_id}/")
    print("   Headers: Authorization: Token {staff_auth_token}")
    print("   Body: {\"status\": \"confirmed\"}")
    print()
    print("3. Patient confirms arrival with GPS:")
    print("   POST /api/patient/confirm-arrival/")
    print("   Headers: Authorization: Token {patient_auth_token}")
    print("   Body: {\"latitude\": 12.345, \"longitude\": 67.890}")

if __name__ == "__main__":
    print("=== Receptionist Token Confirmation Test ===")
    
    # Create a test token
    token = create_test_token()
    
    if token:
        # Test the confirmation process
        success = test_receptionist_confirmation(token)
        
        if success:
            print("\n[SUCCESS] All tests passed!")
        else:
            print("\n[ERROR] Some tests failed!")
            
        # Clean up - delete the test token
        token.delete()
        print(f"[INFO] Cleaned up test token {token.id}")
    
    # Show API usage examples
    show_api_usage()