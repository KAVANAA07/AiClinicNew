"""
Quick Model Verification Script
Tests the trained model with sample predictions
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.waiting_time_predictor import waiting_time_predictor
from api.models import Doctor
from django.utils import timezone
from datetime import time

def verify_model():
    print("=" * 60)
    print("🔍 MODEL VERIFICATION")
    print("=" * 60)
    
    # Check if model files exist
    if not os.path.exists('waiting_time_model.pkl'):
        print("❌ Model file not found!")
        print("   Run: python train_improved_model.py")
        return False
    
    if not os.path.exists('waiting_time_scaler.pkl'):
        print("❌ Scaler file not found!")
        print("   Run: python train_improved_model.py")
        return False
    
    print("✅ Model files found")
    
    # Load model
    if not waiting_time_predictor.load_model():
        print("❌ Failed to load model")
        return False
    
    print("✅ Model loaded successfully")
    
    # Get a doctor for testing
    doctors = Doctor.objects.all()[:3]
    if not doctors:
        print("❌ No doctors found in database")
        return False
    
    print(f"\n📊 Testing predictions with {len(doctors)} doctors...")
    print("-" * 60)
    
    # Test scenarios
    test_scenarios = [
        {"name": "Morning - First Patient", "hour": 9, "minute": 0, "appt_time": time(9, 0)},
        {"name": "Morning - Mid Queue", "hour": 10, "minute": 30, "appt_time": time(10, 30)},
        {"name": "Afternoon - Busy", "hour": 14, "minute": 0, "appt_time": time(14, 0)},
        {"name": "Late Afternoon", "hour": 16, "minute": 30, "appt_time": time(16, 30)},
    ]
    
    all_predictions_valid = True
    
    for doctor in doctors:
        print(f"\n👨‍⚕️ Doctor: {doctor.name}")
        
        for scenario in test_scenarios:
            try:
                # Create test time
                test_time = timezone.now().replace(
                    hour=scenario['hour'],
                    minute=scenario['minute'],
                    second=0,
                    microsecond=0
                )
                
                # Get prediction
                prediction = waiting_time_predictor.predict_waiting_time(
                    doctor_id=doctor.id,
                    current_time=test_time,
                    for_appointment_time=scenario['appt_time']
                )
                
                # Validate prediction
                if prediction < 0 or prediction > 120:
                    print(f"   ⚠️  {scenario['name']}: {prediction} min (OUT OF RANGE)")
                    all_predictions_valid = False
                else:
                    print(f"   ✅ {scenario['name']}: {prediction} min")
                
            except Exception as e:
                print(f"   ❌ {scenario['name']}: ERROR - {e}")
                all_predictions_valid = False
    
    print("\n" + "=" * 60)
    
    if all_predictions_valid:
        print("✅ ALL PREDICTIONS VALID - Model is working correctly!")
        print("=" * 60)
        return True
    else:
        print("⚠️  SOME PREDICTIONS FAILED - Check model training")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = verify_model()
    sys.exit(0 if success else 1)
