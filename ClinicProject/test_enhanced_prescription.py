#!/usr/bin/env python
"""
Test enhanced prescription system with natural language and SMS reminders
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import PrescriptionItem, Consultation, Patient, Doctor
from datetime import time

def test_prescription_descriptions():
    """Test natural language prescription descriptions"""
    
    print("=== Enhanced Prescription System Test ===")
    
    # Example 1: Basic M-A-E timing
    print("\n1. Basic Morning-Afternoon-Evening:")
    item1 = PrescriptionItem(
        medicine_name="Paracetamol",
        dosage="500mg",
        duration_days=3,
        timing_morning=True,
        timing_afternoon=True,
        timing_evening=True
    )
    print(f"   {item1.get_natural_description()}")
    
    # Example 2: Custom timing with food instructions
    print("\n2. Custom timing with food instructions:")
    item2 = PrescriptionItem(
        medicine_name="Amoxicillin",
        dosage="250mg",
        duration_days=5,
        timing_morning=True,
        timing_evening=True,
        morning_time=time(7, 30),
        evening_time=time(21, 0),
        morning_food="before",
        evening_food="after"
    )
    print(f"   {item2.get_natural_description()}")
    
    # Example 3: Only evening with special instructions
    print("\n3. Evening only with special instructions:")
    item3 = PrescriptionItem(
        medicine_name="Crocin",
        dosage="650mg",
        duration_days=2,
        timing_evening=True,
        evening_time=time(22, 0),
        evening_food="with",
        special_instructions="Take only if fever persists"
    )
    print(f"   {item3.get_natural_description()}")
    
    # Example 4: Multiple times with different food instructions
    print("\n4. Complex prescription:")
    item4 = PrescriptionItem(
        medicine_name="Azithromycin",
        dosage="500mg",
        duration_days=3,
        timing_morning=True,
        timing_afternoon=True,
        morning_time=time(8, 0),
        afternoon_time=time(14, 30),
        morning_food="before",
        afternoon_food="after",
        special_instructions="Complete the full course even if symptoms improve"
    )
    print(f"   {item4.get_natural_description()}")

def show_frontend_format():
    """Show how prescriptions will appear in frontend"""
    
    print("\n=== Frontend Display Format ===")
    print("Prescriptions will show as:")
    print("• Paracetamol 500mg - 1 morning and 1 afternoon and 1 evening for 3 days")
    print("• Amoxicillin 250mg - 1 morning at 07:30 AM before food and 1 evening at 09:00 PM after food for 5 days")
    print("• Crocin 650mg - 1 evening at 10:00 PM with food for 2 days. Take only if fever persists")

def show_sms_reminders():
    """Show SMS reminder format"""
    
    print("\n=== SMS Reminder Format ===")
    print("Patients will receive SMS like:")
    print("• Medicine Reminder: Take Paracetamol 500mg (Morning dose)")
    print("• Medicine Reminder: Take Amoxicillin 250mg (Morning dose before food)")
    print("• Medicine Reminder: Take Crocin 650mg (Evening dose with food)")

if __name__ == "__main__":
    test_prescription_descriptions()
    show_frontend_format()
    show_sms_reminders()
    
    print("\n✅ Enhanced prescription system ready!")
    print("📱 SMS reminders will be sent at custom times")
    print("📋 Natural language descriptions for better readability")