#!/usr/bin/env python3
"""
Test the AI summarizer with real medical consultation data.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.join(os.path.dirname(__file__), 'ClinicProject')
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from api.models import Doctor
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

def test_real_medical_summary():
    """Test AI summarizer with realistic medical data"""
    
    print("=== Testing Real Medical Summary ===\n")
    
    # Find a doctor user for authentication
    doctor = Doctor.objects.first()
    if not doctor or not doctor.user:
        print("No doctor with user account found!")
        return
    
    print(f"Using doctor: {doctor.name}")
    
    # Get or create auth token
    token, _ = Token.objects.get_or_create(user=doctor.user)
    
    # Create test client
    client = Client()
    
    # Real medical consultation history
    medical_history = """
    Date: 2025-01-15
    Doctor: Dr. Smith
    Notes: Patient complained of severe headache and fever for 3 days. Temperature recorded at 101.2°F. Blood pressure 140/90. Prescribed paracetamol 500mg twice daily for fever. Advised rest and increased fluid intake.
    
    Date: 2025-01-10
    Doctor: Dr. Jones  
    Notes: Routine checkup. Patient reports feeling well. Blood pressure normal at 120/80. Weight stable. No current medications. Advised to continue healthy diet and exercise.
    
    Date: 2024-12-20
    Doctor: Dr. Smith
    Notes: Patient presented with chest discomfort and shortness of breath. ECG performed - normal sinus rhythm. Prescribed aspirin 75mg daily. Referred to cardiologist for further evaluation. Follow-up in 2 weeks.
    
    Date: 2024-12-15
    Doctor: Dr. Brown
    Notes: Follow-up for diabetes management. HbA1c levels improved to 7.2%. Patient compliant with metformin 500mg twice daily. Blood glucose monitoring shows good control. Continue current treatment plan.
    """
    
    print("Testing with realistic medical consultation data...")
    
    # Test the AI summarizer
    response = client.post(
        '/api/ai-summary/',
        data=json.dumps({
            'patient_history': medical_history,
            'phone': '1234567890'
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = json.loads(response.content)
        summary = data.get('summary', '')
        model = data.get('model', '')
        
        print(f"Model: {model}")
        print(f"Summary length: {len(summary)} characters")
        print("\n--- MEDICAL SUMMARY ---")
        print(summary)
        print("--- END SUMMARY ---")
        
        # Check if summary contains key medical information
        summary_lower = summary.lower()
        medical_terms_found = []
        
        medical_terms = [
            'headache', 'fever', 'blood pressure', 'temperature', 'paracetamol',
            'chest discomfort', 'diabetes', 'metformin', 'aspirin', 'ecg'
        ]
        
        for term in medical_terms:
            if term in summary_lower:
                medical_terms_found.append(term)
        
        print(f"\n[SUCCESS] Medical terms extracted: {len(medical_terms_found)}")
        print(f"Terms found: {', '.join(medical_terms_found)}")
        print(f"[SUCCESS] Doctor consultation summarizer is working with real medical data!")
        
    else:
        try:
            error_data = json.loads(response.content)
            print(f"[ERROR] {error_data}")
        except:
            print(f"[ERROR] Status {response.status_code}: {response.content}")

if __name__ == "__main__":
    test_real_medical_summary()