#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.waiting_time_predictor import waiting_time_predictor, ML_AVAILABLE
from api.models import Token
from django.utils import timezone
from datetime import timedelta

print("=== ML WAITING TIME PREDICTION STATUS ===\n")

# Check ML dependencies
print(f"1. ML Dependencies Available: {ML_AVAILABLE}")
if not ML_AVAILABLE:
    print("   [ERROR] Install with: pip install pandas scikit-learn joblib")
else:
    print("   [OK] pandas, scikit-learn, joblib are installed")

# Check model files
model_exists = os.path.exists(waiting_time_predictor.model_path)
scaler_exists = os.path.exists(waiting_time_predictor.scaler_path)

print(f"\n2. Model Files:")
print(f"   Model file exists: {model_exists}")
print(f"   Scaler file exists: {scaler_exists}")

if model_exists:
    print(f"   Model path: {os.path.abspath(waiting_time_predictor.model_path)}")
if scaler_exists:
    print(f"   Scaler path: {os.path.abspath(waiting_time_predictor.scaler_path)}")

# Check training data
print(f"\n3. Training Data Analysis:")

# All completed tokens
all_completed = Token.objects.filter(
    status='completed',
    completed_at__isnull=False
).count()

# Recent completed tokens (last 30 days)
end_date = timezone.now().date()
start_date = end_date - timedelta(days=30)
recent_completed = Token.objects.filter(
    created_at__date__gte=start_date,
    status='completed',
    completed_at__isnull=False
).count()

print(f"   Total completed consultations: {all_completed}")
print(f"   Recent completed (30 days): {recent_completed}")
print(f"   Minimum required for training: 10")

if all_completed >= 10:
    print("   [OK] Sufficient data for training")
else:
    print("   [ERROR] Insufficient data - need more completed consultations")

# Test prediction
print(f"\n4. Prediction Test:")
try:
    from api.models import Doctor
    doctor = Doctor.objects.first()
    if doctor:
        prediction = waiting_time_predictor.predict_waiting_time(doctor.id)
        print(f"   Sample prediction for Dr. {doctor.name}: {prediction} minutes")
        
        # Check if using ML or fallback
        if ML_AVAILABLE and model_exists and scaler_exists:
            print("   Using: ML Model")
        else:
            print("   Using: Simple Fallback Logic")
    else:
        print("   No doctors found in database")
except Exception as e:
    print(f"   Error: {e}")

# Training recommendation
print(f"\n5. Recommendations:")
if not ML_AVAILABLE:
    print("   📦 Install ML dependencies: pip install pandas scikit-learn joblib")
elif all_completed < 10:
    print("   📊 Complete more consultations to generate training data")
elif not model_exists:
    print("   🤖 Train the model: python manage.py shell -c \"from api.waiting_time_predictor import waiting_time_predictor; waiting_time_predictor.train_model()\"")
else:
    print("   [OK] System is ready for ML predictions")

print("\n=== END STATUS CHECK ===")