#!/usr/bin/env python
"""
Test script to verify consistent waiting time predictions
"""
import os
import sys
import django
from datetime import datetime, time

# Setup Django
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Doctor, Patient
from api.waiting_time_predictor import waiting_time_predictor
from django.utils import timezone

def test_prediction_consistency():
    """Test that predictions are consistent between different calls"""
    
    print("🔍 Testing Waiting Time Prediction Consistency")
    print("=" * 60)
    
    try:
        doctor = Doctor.objects.first()
        if not doctor:
            print("❌ No doctors found in database")
            return
        
        print(f"📋 Testing with Doctor: {doctor.name} (ID: {doctor.id})")
        
        # Test appointment time
        appointment_time = time(21, 50)
        current_time = timezone.now()
        
        print(f"⏰ Testing appointment time: {appointment_time}")
        print(f"🕐 Current time: {current_time.strftime('%H:%M')}")
        
        # Check current queue
        today = current_time.date()
        current_queue = Token.objects.filter(
            doctor=doctor,
            date=today,
            status__in=['waiting', 'confirmed', 'in_consultation']
        )
        
        print(f"📊 Current queue length: {current_queue.count()}")
        
        # Test 1: Direct prediction call (like widget)
        print("\n🔧 Test 1: Direct prediction call (widget style)")
        prediction1 = waiting_time_predictor.predict_waiting_time(
            doctor.id,
            current_time=current_time,
            for_appointment_time=appointment_time
        )
        print(f"   Result: {prediction1} minutes")
        
        # Test 2: Same call with explicit parameters (like token creation)
        print("\n🔧 Test 2: Token creation style prediction")
        prediction2 = waiting_time_predictor.predict_waiting_time(
            doctor.id,
            current_time=current_time,
            for_appointment_time=appointment_time
        )
        print(f"   Result: {prediction2} minutes")
        
        # Test 3: Without appointment time (walk-in)
        print("\n🔧 Test 3: Walk-in prediction")
        prediction3 = waiting_time_predictor.predict_waiting_time(
            doctor.id,
            current_time=current_time
        )
        print(f"   Result: {prediction3} minutes")
        
        # Check consistency
        print("\n" + "=" * 60)
        print("📈 Results Summary:")
        print(f"   Widget prediction:      {prediction1} minutes")
        print(f"   Token creation:         {prediction2} minutes")
        print(f"   Walk-in prediction:     {prediction3} minutes")
        
        if prediction1 == prediction2:
            print("   ✅ PASS: Widget and token creation predictions match!")
        else:
            print(f"   ❌ FAIL: Predictions don't match ({prediction1} vs {prediction2})")
        
        if prediction1 and prediction1 <= 15 and current_queue.count() == 0:
            print("   ✅ PASS: Empty queue gives reasonable prediction")
        else:
            print(f"   ⚠️  WARNING: High prediction ({prediction1} min) for empty queue")
        
        # Check queue calculation
        patients_before = current_queue.filter(
            appointment_time__lt=appointment_time
        ).count()
        
        print(f"\n📋 Queue Analysis:")
        print(f"   Patients before 21:50: {patients_before}")
        print(f"   Total active patients: {current_queue.count()}")
        
        if patients_before == 0 and prediction1 and prediction1 <= 15:
            print("   ✅ OVERALL: Predictions are now accurate and consistent!")
        else:
            print("   ❌ OVERALL: Still needs adjustment")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prediction_consistency()