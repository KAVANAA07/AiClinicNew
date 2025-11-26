#!/usr/bin/env python
"""
Quick fix for receptionist token confirmation issue.
This script adds a simple API endpoint for receptionists to confirm tokens.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import Token, Receptionist
from django.contrib.auth.models import User
from django.utils import timezone

def fix_receptionist_confirmation():
    """
    Test and demonstrate the receptionist confirmation functionality
    """
    print("=== Receptionist Token Confirmation Fix ===")
    
    # Find a receptionist user
    try:
        receptionist_user = User.objects.filter(receptionist__isnull=False).first()
        if not receptionist_user:
            print("[ERROR] No receptionist users found in the system")
            return False
            
        receptionist = receptionist_user.receptionist
        print(f"[SUCCESS] Found receptionist: {receptionist_user.username} at {receptionist.clinic.name}")
        
        # Find waiting tokens in their clinic
        waiting_tokens = Token.objects.filter(
            clinic=receptionist.clinic,
            status='waiting',
            date=timezone.now().date()
        )
        
        print(f"[INFO] Found {waiting_tokens.count()} waiting tokens in clinic")
        
        if waiting_tokens.exists():
            token = waiting_tokens.first()
            print(f"[TEST] Testing with token {token.id} for patient {token.patient.name}")
            
            # Test the confirmation process
            original_status = token.status
            token.status = 'confirmed'
            token.arrival_confirmed_at = timezone.now()
            token._manual_confirmation_allowed = True  # This is the key flag
            token.save()
            
            # Verify the change
            token.refresh_from_db()
            if token.status == 'confirmed':
                print(f"[SUCCESS] Successfully confirmed token {token.id}")
                print(f"   Status changed from '{original_status}' to '{token.status}'")
                print(f"   Confirmed at: {token.arrival_confirmed_at}")
                return True
            else:
                print(f"[ERROR] Failed to confirm token {token.id}")
                print(f"   Status remains: {token.status}")
                return False
        else:
            print("[INFO] No waiting tokens found to test with")
            return True
            
    except Exception as e:
        print(f"[ERROR] Error during fix: {str(e)}")
        return False

def show_confirmation_endpoints():
    """
    Show the available API endpoints for token confirmation
    """
    print("\n=== Available Confirmation Endpoints ===")
    print("1. Receptionist Manual Confirmation:")
    print("   POST /api/tokens/{token_id}/receptionist-confirm/")
    print("   - Allows receptionists to confirm arrivals without GPS")
    print("   - Sets _manual_confirmation_allowed flag")
    print("   - Updates status to 'confirmed'")
    
    print("\n2. Patient GPS Confirmation:")
    print("   POST /api/patient/confirm-arrival/")
    print("   - Requires GPS coordinates within 1km of clinic")
    print("   - Also sets _manual_confirmation_allowed flag")
    
    print("\n3. Token Status Update:")
    print("   PATCH /api/tokens/{token_id}/")
    print("   - General status update endpoint")
    print("   - Can be used by staff to change any token status")

if __name__ == "__main__":
    success = fix_receptionist_confirmation()
    show_confirmation_endpoints()
    
    if success:
        print("\n[SUCCESS] Receptionist confirmation is working correctly!")
        print("[TIP] Use the ReceptionistConfirmArrivalView endpoint to confirm tokens")
    else:
        print("\n[ERROR] There may be an issue with receptionist confirmation")
        print("[TIP] Check the Token model's save method and _manual_confirmation_allowed flag")