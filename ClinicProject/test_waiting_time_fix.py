#!/usr/bin/env python
"""
Test script to verify waiting time prediction accuracy
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

def test_waiting_time_prediction():
    """Test waiting time prediction with different scenarios"""
    
    print("🔍 Testing Waiting Time Prediction Fix")
    print("=" * 50)
    
    # Get a doctor for testing
    try:
        doctor = Doctor.objects.first()
        if not doctor:
            print("❌ No doctors found in database")
            return
        
        print(f"📋 Testing with Doctor: {doctor.name} (ID: {doctor.id})")
        
        # Test Case 1: No queue, future appointment
        print("\n📅 Test Case 1: Future appointment (21:50) with no queue")
        appointment_time = time(21, 50)
        
        # Check current queue
        today = timezone.now().date()
        current_queue = Token.objects.filter(
            doctor=doctor,
            date=today,
            status__in=['waiting', 'confirmed', 'in_consultation']
        )
        
        print(f"   Current queue length: {current_queue.count()}")
        
        # Get prediction
        predicted_wait = waiting_time_predictor.predict_waiting_time(
            doctor.id,
            for_appointment_time=appointment_time
        )
        
        print(f"   Predicted wait time: {predicted_wait} minutes")
        
        if predicted_wait and predicted_wait <= 15:
            print("   ✅ PASS: Prediction is reasonable for empty queue")
        else:
            print(f"   ❌ FAIL: Prediction too high ({predicted_wait} min) for empty queue")
        
        # Test Case 2: No appointment time (walk-in)
        print("\n🚶 Test Case 2: Walk-in patient with no queue")
        
        predicted_wait_walkin = waiting_time_predictor.predict_waiting_time(doctor.id)
        print(f"   Predicted wait time for walk-in: {predicted_wait_walkin} minutes")
        
        if predicted_wait_walkin and predicted_wait_walkin <= 15:
            print("   ✅ PASS: Walk-in prediction is reasonable for empty queue")
        else:
            print(f"   ❌ FAIL: Walk-in prediction too high ({predicted_wait_walkin} min) for empty queue")
        
        # Test Case 3: Check queue calculation
        print("\n📊 Test Case 3: Queue position calculation")
        
        # Check patients before 21:50
        patients_before = current_queue.filter(
            appointment_time__lt=appointment_time
        ).count()
        
        print(f"   Patients scheduled before 21:50: {patients_before}")
        
        if patients_before == 0:
            print("   ✅ PASS: No patients before appointment time")
        else:
            print(f"   ⚠️  WARNING: {patients_before} patients scheduled before 21:50")
            for token in current_queue.filter(appointment_time__lt=appointment_time):
                print(f"      - {token.patient.name} at {token.appointment_time}")
        
        print("\n" + "=" * 50)
        print("🎯 Summary:")
        print(f"   - Empty queue prediction: {predicted_wait} minutes")
        print(f"   - Walk-in prediction: {predicted_wait_walkin} minutes")
        print(f"   - Patients before 21:50: {patients_before}")
        
        if predicted_wait and predicted_wait <= 15 and patients_before == 0:
            print("   ✅ Overall: FIXED - Predictions are now accurate!")
        else:
            print("   ❌ Overall: Still needs adjustment")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_waiting_time_prediction()