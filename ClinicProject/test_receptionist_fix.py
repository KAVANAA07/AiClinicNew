#!/usr/bin/env python
"""
Test the receptionist status update fix
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import Token, Patient, Doctor, Clinic
from django.utils import timezone

def test_status_update():
    """Test direct status update with manual flag"""
    
    # Find or create test data
    clinic = Clinic.objects.first()
    doctor = Doctor.objects.filter(clinic=clinic).first() if clinic else None
    
    if not doctor:
        print("[ERROR] No doctor found")
        return False
        
    patient, _ = Patient.objects.get_or_create(
        phone_number="+1234567890",
        defaults={'name': 'Test Patient', 'age': 30}
    )
    
    # Create test token
    token = Token.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        date=timezone.now().date(),
        status='waiting'
    )
    
    print(f"[INFO] Created token {token.id} with status: {token.status}")
    
    # Test the fix - simulate what the API does
    token.status = 'confirmed'
    token._manual_confirmation_allowed = True  # This is the key fix
    token.arrival_confirmed_at = timezone.now()
    token.save()
    
    # Verify
    token.refresh_from_db()
    print(f"[INFO] Token status after update: {token.status}")
    print(f"[INFO] Arrival confirmed at: {token.arrival_confirmed_at}")
    
    success = token.status == 'confirmed'
    
    # Cleanup
    token.delete()
    
    return success

if __name__ == "__main__":
    print("=== Testing Receptionist Status Update Fix ===")
    
    success = test_status_update()
    
    if success:
        print("[SUCCESS] Receptionist can now update token status!")
    else:
        print("[ERROR] Status update still failing!")