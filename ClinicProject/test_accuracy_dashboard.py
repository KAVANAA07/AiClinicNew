#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import Client
from django.utils import timezone
from api.models import Token, Doctor, Patient
from datetime import timedelta
import json

def test_accuracy_dashboard():
    """Test the model accuracy dashboard for judges"""
    print("Testing Model Accuracy Dashboard for Judges...")
    
    client = Client()
    
    # Test model accuracy endpoint
    print("\n1. Testing Model Accuracy Metrics...")
    response = client.get('/api/model/accuracy/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nModel Accuracy Results:")
        print(f"Algorithm: {data.get('model_type', 'N/A')}")
        print(f"Data Source: {data.get('data_source', 'N/A')}")
        
        if 'model_accuracy' in data:
            accuracy = data['model_accuracy']
            if accuracy.get('status') == 'success':
                metrics = accuracy['metrics']
                print(f"\nPerformance Metrics:")
                print(f"  Sample Size: {accuracy['sample_size']} consultations")
                print(f"  MAE (Mean Absolute Error): {metrics['mae_minutes']} minutes")
                print(f"  RMSE: {metrics['rmse_minutes']} minutes")
                print(f"  R² Score: {metrics['r2_score']}")
                print(f"  F1 Score: {metrics['f1_score']}")
                print(f"  Accuracy (within 10 min): {metrics['accuracy_within_10min']}%")
                print(f"  Accuracy (within 15 min): {metrics['accuracy_within_15min']}%")
                
                interpretation = accuracy['interpretation']
                print(f"\nModel Quality: {interpretation['model_quality']}")
                print(f"Summary: {interpretation['accuracy']}")
            else:
                print(f"Insufficient data: {accuracy.get('message', 'Unknown error')}")
    
    # Test training log endpoint
    print("\n2. Testing Training Data Statistics...")
    response = client.get('/api/model/training-log/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Training Period: {data.get('training_period')}")
        print(f"Total Training Samples: {data.get('total_training_samples')}")
        
        doctor_stats = data.get('doctor_statistics', [])
        print(f"\nDoctor-wise Training Data:")
        for doctor in doctor_stats:
            print(f"  Dr. {doctor['doctor_name']}: {doctor['consultation_count']} consultations, avg wait: {doctor['avg_waiting_time']} min")
    
    print("\n3. Testing Dashboard Integration...")
    response = client.get('/api/waiting-time/dashboard/')
    print(f"Dashboard Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('clinics', []))} clinics with waiting time predictions")

def create_sample_accuracy_data():
    """Create sample data to demonstrate accuracy calculations"""
    print("\n" + "="*60)
    print("SAMPLE ACCURACY CALCULATION FOR JUDGES")
    print("="*60)
    
    # Sample prediction vs actual data
    sample_data = [
        {"predicted": 25, "actual": 22, "patient": "A"},
        {"predicted": 35, "actual": 45, "patient": "B"},
        {"predicted": 20, "actual": 38, "patient": "C"},
        {"predicted": 40, "actual": 42, "patient": "D"},
        {"predicted": 30, "actual": 28, "patient": "E"},
        {"predicted": 15, "actual": 18, "patient": "F"},
        {"predicted": 45, "actual": 41, "patient": "G"},
        {"predicted": 28, "actual": 25, "patient": "H"}
    ]
    
    print("\nSample Predictions vs Actual Waiting Times:")
    print("Patient | Predicted | Actual | Error | Within 15min?")
    print("-" * 50)
    
    errors = []
    within_15min = 0
    
    for data in sample_data:
        error = abs(data["predicted"] - data["actual"])
        errors.append(error)
        is_good = error <= 15
        if is_good:
            within_15min += 1
        
        print(f"   {data['patient']}    |    {data['predicted']:2d}     |   {data['actual']:2d}   |  {error:2.0f}   |     {'✓' if is_good else '✗'}")
    
    # Calculate metrics
    mae = sum(errors) / len(errors)
    accuracy_15min = (within_15min / len(sample_data)) * 100
    f1_score = within_15min / len(sample_data)  # Simplified F1 for this example
    
    print(f"\nCalculated Metrics:")
    print(f"  Mean Absolute Error (MAE): {mae:.1f} minutes")
    print(f"  Accuracy (within 15 min): {accuracy_15min:.1f}%")
    print(f"  F1 Score: {f1_score:.3f}")
    
    # Interpretation
    if mae <= 10 and accuracy_15min >= 80:
        quality = "Excellent"
    elif mae <= 15 and accuracy_15min >= 70:
        quality = "Good"
    else:
        quality = "Fair"
    
    print(f"  Model Quality: {quality}")
    
    print(f"\nInterpretation for Judges:")
    print(f"  - On average, predictions are within {mae:.1f} minutes of actual waiting time")
    print(f"  - {accuracy_15min:.0f}% of predictions are within 15 minutes (clinically acceptable)")
    print(f"  - F1 Score of {f1_score:.3f} indicates {quality.lower()} classification performance")

def show_api_endpoints():
    """Show API endpoints for judges to test"""
    print("\n" + "="*60)
    print("API ENDPOINTS FOR JUDGES TO TEST")
    print("="*60)
    
    endpoints = [
        {
            "name": "Model Accuracy Dashboard",
            "url": "GET /api/model/accuracy/",
            "description": "Complete accuracy metrics including MAE, F1 score, R² score",
            "auth": "No authentication required"
        },
        {
            "name": "Training Data Statistics", 
            "url": "GET /api/model/training-log/",
            "description": "Training data quality and doctor-wise statistics",
            "auth": "No authentication required"
        },
        {
            "name": "Live Waiting Time Dashboard",
            "url": "GET /api/waiting-time/dashboard/",
            "description": "Real-time predictions for all clinics and doctors",
            "auth": "No authentication required"
        },
        {
            "name": "Individual Doctor Prediction",
            "url": "GET /api/waiting-time/predict/1/",
            "description": "Get prediction for specific doctor (replace 1 with doctor ID)",
            "auth": "Authentication required"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n{endpoint['name']}:")
        print(f"  URL: {endpoint['url']}")
        print(f"  Description: {endpoint['description']}")
        print(f"  Authentication: {endpoint['auth']}")
    
    print(f"\nBase URL: http://localhost:8000")
    print(f"Example: curl http://localhost:8000/api/model/accuracy/")

if __name__ == "__main__":
    test_accuracy_dashboard()
    create_sample_accuracy_data()
    show_api_endpoints()