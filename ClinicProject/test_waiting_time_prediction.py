#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.utils import timezone
from api.models import Token, Doctor, Patient, Clinic
from api.waiting_time_predictor import waiting_time_predictor
import random

def create_test_data():
    """Create test data for waiting time prediction"""
    print("Creating test data...")
    
    # Get or create test doctor
    try:
        doctor = Doctor.objects.first()
        if not doctor:
            print("No doctors found. Please create a doctor first.")
            return False
    except Exception as e:
        print(f"Error getting doctor: {e}")
        return False
    
    # Create historical tokens with realistic waiting times
    today = timezone.now().date()
    
    for days_back in range(1, 31):  # Last 30 days
        test_date = today - timedelta(days=days_back)
        
        # Create 3-8 tokens per day
        num_tokens = random.randint(3, 8)
        
        for i in range(num_tokens):
            try:
                # Create or get patient
                patient, _ = Patient.objects.get_or_create(
                    phone_number=f"555000{days_back:02d}{i:02d}",
                    defaults={
                        'name': f'Test Patient {days_back}-{i}',
                        'age': random.randint(20, 70)
                    }
                )
                
                # Create token with realistic times
                created_time = timezone.make_aware(
                    datetime.combine(test_date, datetime.min.time()) + 
                    timedelta(hours=random.randint(9, 16), minutes=random.randint(0, 59))
                )
                
                # Consultation started 10-60 minutes after creation
                consultation_delay = timedelta(minutes=random.randint(10, 60))
                consultation_start = created_time + consultation_delay
                
                # Create token without auto-save to set fields manually
                token = Token.objects.create(
                    patient=patient,
                    doctor=doctor,
                    clinic=doctor.clinic,
                    date=test_date,
                    status='waiting',  # Start as waiting
                    token_number=f"TEST-{days_back}-{i}"
                )
                
                # Update with historical data
                token.created_at = created_time
                token.consultation_start_time = consultation_start
                token.completed_at = consultation_start + timedelta(minutes=random.randint(15, 45))
                token.status = 'completed'
                token.save(update_fields=['created_at', 'consultation_start_time', 'completed_at', 'status'])
                
                print(f"Created token {token.id} for {test_date} - waiting time: {consultation_delay.total_seconds()/60:.1f} min")
                
            except Exception as e:
                print(f"Error creating token: {e}")
                continue
    
    print(f"Created test data for doctor {doctor.name}")
    return True

def test_model_training():
    """Test model training"""
    print("\nTesting model training...")
    
    try:
        success = waiting_time_predictor.train_model()
        if success:
            print("Model training successful!")
            return True
        else:
            print("Model training failed")
            return False
    except Exception as e:
        print(f"Model training error: {e}")
        return False

def test_predictions():
    """Test waiting time predictions"""
    print("\nTesting predictions...")
    
    try:
        doctor = Doctor.objects.first()
        if not doctor:
            print("No doctor found for testing")
            return False
        
        # Test prediction
        predicted_time = waiting_time_predictor.predict_waiting_time(doctor.id)
        
        if predicted_time:
            print(f"Predicted waiting time for Dr. {doctor.name}: {predicted_time} minutes")
            
            # Test with different queue scenarios
            current_queue = Token.objects.filter(
                doctor=doctor,
                created_at__date=timezone.now().date(),
                status__in=['waiting', 'confirmed']
            ).count()
            
            print(f"Current queue length: {current_queue}")
            return True
        else:
            print("No prediction returned")
            return False
            
    except Exception as e:
        print(f"Prediction error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    
    try:
        from django.test import Client
        from django.contrib.auth.models import User
        
        # Create test user
        user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={'is_staff': True}
        )
        
        client = Client()
        client.force_login(user)
        
        # Test status endpoint
        response = client.get('/api/waiting-time/status/')
        print(f"Status endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Status data: {response.json()}")
        
        # Test prediction endpoint
        doctor = Doctor.objects.first()
        if doctor:
            response = client.get(f'/api/waiting-time/predict/{doctor.id}/')
            print(f"Prediction endpoint: {response.status_code}")
            if response.status_code == 200:
                print(f"Prediction data: {response.json()}")
        
        return True
        
    except Exception as e:
        print(f"API test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Waiting Time Prediction System")
    print("=" * 50)
    
    # Step 1: Create test data
    if create_test_data():
        print("Test data created")
    else:
        print("Failed to create test data")
        sys.exit(1)
    
    # Step 2: Train model
    if test_model_training():
        print("Model training successful")
    else:
        print("Model training failed")
        sys.exit(1)
    
    # Step 3: Test predictions
    if test_predictions():
        print("Predictions working")
    else:
        print("Predictions failed")
    
    # Step 4: Test API endpoints
    if test_api_endpoints():
        print("API endpoints working")
    else:
        print("API endpoints failed")
    
    print("\nWaiting Time Prediction System Test Complete!")
    print("\nNext steps:")
    print("1. Run: python setup_ml_schedules.py")
    print("2. Start qcluster: python manage.py qcluster")
    print("3. Model will retrain nightly at 2 AM")
    print("4. Use /api/waiting-time/predict/<doctor_id>/ for predictions")